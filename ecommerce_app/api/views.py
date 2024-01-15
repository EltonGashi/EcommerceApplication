from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser , AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from ecommerce_app.models import (
    Product, Order, Cart, CartItem, Payment, Review, Wishlist, ContactMessage
)
from ecommerce_app.api.serializers import (
    ProductSerializer, OrderSerializer, CartSerializer, CartItemSerializer,
    PaymentSerializer, CartPaymentSerializer ,ReviewSerializer,
    WishlistSerializer
)
from django.http import Http404, JsonResponse
from django.conf import settings
import stripe
from django.contrib.auth.models import AnonymousUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.exceptions import ValidationError
from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from fuzzywuzzy import fuzz

from .forms import ContactForm
from django.core.mail import send_mail
from rest_framework.decorators import api_view, permission_classes
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt



#---------------------------- Product Views -------------------------------------


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]  # Add SearchFilter and DjangoFilterBackend
    search_fields = ['name']  # Specify the fields you want to search

    def get_queryset(self):
        # Get the 'category' and 'search' parameters from the request's query parameters
        category = self.request.query_params.get('category')
        search_term = self.request.query_params.get('search')

        # If a category is specified, filter the queryset by that category
        queryset = Product.objects.all()
        if category:
            queryset = queryset.filter(category=category)

        # If a search term is specified, perform a fuzzy search
        if search_term:
            queryset = self.fuzzy_search(queryset, 'name', search_term)

        return queryset

    def fuzzy_search(self, queryset, field, search_term):
        # Perform fuzzy search using fuzzywuzzy's process method
        results = []
        for item in queryset:
            ratio = fuzz.partial_ratio(search_term.lower(), getattr(item, field).lower())
            if ratio >= 80:  # You can adjust the threshold as needed
                results.append(item)

        # Check if there are any matching items
        if not results:
            return queryset.none()

        # Create a new queryset with the matched items
        matched_items = Product.objects.filter(pk__in=[item.pk for item in results])

        # Return the queryset of matched items
        return matched_items

class ProductDetailView(RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Provide a default queryset for all users
        return Product.objects.all()

class ProductCreateView(CreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def perform_create(self, serializer):
        # Set the user field based on the authenticated user
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Add logic to set the category from the request data
        request_data = request.data
        category = request_data.get('category')

        if not category:
            raise serializers.ValidationError("Category is required.")

        request_data['category'] = category
        return super().create(request, *args, **kwargs)


class ProductUpdateView(UpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

class ProductDeleteView(DestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def perform_destroy(self, instance):
        instance.delete()
        return Response({'message': 'Product deleted successfully'}, status=status.HTTP_200_OK)



#---------------------------- Order Views -------------------------------------


class OrderListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return Order.objects.all()
            return Order.objects.filter(user=self.request.user)
        else:
            return Order.objects.none()

class OrderDetailView(RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            raise Http404("You are not authenticated.")

        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

class OrderCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def perform_create(self, serializer):
        # Automatically set the user as the authenticated user
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Override the create method to handle the response
        serializer = self.get_serializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)

        # Calculate the total amount based on the prices of products in the order
        products_data = serializer.validated_data['products']
        total_amount = sum(Product.objects.get(pk=product['product']).price * product['quantity'] for product in products_data)

        # Update the amount field in the serializer data
        serializer.validated_data['amount'] = total_amount

        self.check_stock_availability(products_data)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def check_stock_availability(self, products_data):
        for product_data in products_data:
            try:
                # Assuming product ID is directly present in the product data
                product_id = product_data['product']
                quantity = product_data['quantity']

                product = Product.objects.get(pk=product_id)

                if quantity > product.stock_quantity:
                    raise serializers.ValidationError({'detail': f"Not enough stock for product {product.name}. Available stock: {product.stock_quantity}"})
            except KeyError:
                raise serializers.ValidationError({'detail': "Product data is missing the required fields."})
            except Product.DoesNotExist:
                raise serializers.ValidationError({'detail': f"Product with ID {product_id} does not exist."})
            
            
class OrderUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if the user is the owner of the order
        if request.user != instance.user:
            raise Http404("You do not have permission to perform this action.")

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if 'is_shipped' in request.data and request.data['is_shipped']:
            instance.mark_as_shipped()

        self.perform_update(serializer)

        return Response(serializer.data)

class OrderDeleteView(DestroyAPIView):
    permission_classes = [IsAuthenticated | IsAdminUser]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def perform_destroy(self, instance):
        # Check if the user is the owner of the order or an admin
        if self.request.user != instance.user and not self.request.user.is_staff:
            raise Http404("You do not have permission to perform this action.")

        instance.delete()
        return Response({'message': 'Order deleted successfully'}, status=status.HTTP_200_OK)


#---------------------------- Cart Views -------------------------------------

class CartDetailView(RetrieveAPIView):
    serializer_class = CartSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated and user.is_staff:
            # Admin can view all carts
            return Cart.objects.all()
        elif user.is_authenticated:
            # Regular user can view only their own cart
            return Cart.objects.filter(user=user)
        else:
            # Anonymous user has no access
            return Cart.objects.none()
    
    
    
class CartAddProductView(CreateAPIView):
    permission_classes = [IsAuthenticated | IsAdminUser]
    serializer_class = CartItemSerializer

    def create(self, request, *args, **kwargs):
        products_data = request.data.get('products', [])  # Assume 'products' is a list of product IDs with quantities

        if not products_data:
            return Response({'detail': 'No products provided'}, status=status.HTTP_400_BAD_REQUEST)

        cart = self.get_or_create_cart()

        for product_entry in products_data:
            product_id = product_entry.get('product')
            quantity = product_entry.get('quantity', 1)  # Default to 1 if quantity is not provided

            # You can perform additional validation here, such as checking if the product exists
            product = Product.objects.get(pk=product_id)
            cart_item, created = CartItem.objects.get_or_create(product=product, cart=cart, defaults={'quantity': quantity})

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_or_create_cart(self):
        user = self.request.user
        cart, created = Cart.objects.get_or_create(user=user)
        if created:
            print(f"A new cart was created for user: {user}")
        return cart

class CartRemoveProductView(DestroyAPIView):
    permission_classes = [IsAuthenticated | IsAdminUser]
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if the user is the owner of the cart or an admin
        if request.user != instance.cart.user and not request.user.is_staff:
            raise PermissionDenied("You do not have permission to remove this product from the cart.")

        if instance:
            instance.delete()
            return Response({'message': 'CartItem deleted successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'CartItem not found'}, status=status.HTTP_404_NOT_FOUND)

class CartUpdateProductQuantityView(UpdateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated | IsAdminUser]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_quantity = request.data.get('quantity')

        # Check if the user is the owner of the cart or an admin
        if request.user != instance.cart.user and not request.user.is_staff:
            raise PermissionDenied("You do not have permission to update the quantity in this cart.")

        # Perform the quantity update
        instance.quantity = new_quantity
        instance.save()

        serializer = CartItemSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

#-------------------------------------------------------------------------------------------
class CartItemCreateView(CreateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    def perform_create(self, serializer):
        cart = Cart.objects.get_or_create(user=self.request.user)[0]
        serializer.save(cart=cart)

class CartItemUpdateView(UpdateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

class CartItemDeleteView(DestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

class CartItemListAPIView(ListAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=user_cart)
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
#----------------------------------------------------------------------------------------------------------

class PaymentProcessView(CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        order = serializer.validated_data['order']

        # Check if the user is the owner of the order or an admin
        if not (self.request.user.is_staff or self.request.user == order.user):
            raise PermissionDenied("You do not have permission to perform this action.")

        # Check if the user is authenticated
        if not self.request.user.is_authenticated or isinstance(self.request.user, AnonymousUser):
            raise PermissionDenied("You must be authenticated to perform this action.")

        serializer.validated_data['user'] = self.request.user

        # Process payment using the Stripe API
        stripe.api_key = 'sk_test_51OUyI5AB7c17WEYMRRxRm8yzPacZzdeunwydgwZ2fEPnI44kgkpYvw0irY0DLse5ZdDlT60S8D7JZeB0raBK7Hm100HOWFGP5x'  # Replace with your actual Stripe secret key
        stripe_token = serializer.validated_data['stripe_token']

        try:
            total_amount = 0

            # Calculate the total amount based on the products in the order
            for product in order.products.all():
                total_amount += product.price * product.stock_quantity  # Assuming you have a unit_price field in your Product model

            charge = stripe.Charge.create(
                amount=int(total_amount * 100),  # Convert amount to cents
                currency='usd',
                source=stripe_token,
                description='Payment for Order #{}'.format(order.id),
            )

            # Set the shipping date to today + 3 days (you can adjust this logic based on your requirements)
            shipping_date = datetime.now() + timedelta(days=3)

            transaction_details = {
                'charge_id': charge.id,
                'payment_status': charge.status,
                'shipping_date': shipping_date.strftime('%Y-%m-%d %H:%M:%S'),  # Convert datetime to string
                'payment_amount': total_amount,  # Total amount based on the products in the order
            }
            serializer.save(transaction_details=transaction_details, status='success')

        except stripe.error.CardError as e:
            # Handle card error
            serializer.save(transaction_details={'error': str(e)}, status='failed')
            raise serializers.ValidationError({'detail': 'Payment failed. {}'.format(str(e))})
        
class CartPaymentProcessView(CreateAPIView):
    serializer_class = CartPaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_cart(self, cart_id):
        try:
            cart = Cart.objects.get(id=cart_id, user=self.request.user)
            return cart
        except Cart.DoesNotExist:
            raise PermissionDenied("Invalid cart ID.")

    def create_order(self, cart):
        order = Order.objects.create(user=self.request.user, amount=0, status='pending')

        for cart_item in cart.cart_items.all():
            order.amount += cart_item.product.price * cart_item.quantity

        order.save()
        return order

    def process_payment(self, order, stripe_token):
        stripe.api_key = 'sk_test_51OUyI5AB7c17WEYMRRxRm8yzPacZzdeunwydgwZ2fEPnI44kgkpYvw0irY0DLse5ZdDlT60S8D7JZeB0raBK7Hm100HOWFGP5x'

        try:
            # Ensure the amount is a positive integer
            amount_in_cents = int(order.amount * 100)
            if amount_in_cents < 1:
                raise ValueError("Invalid amount value")

            charge = stripe.Charge.create(
                amount=amount_in_cents,
                currency='usd',
                source=stripe_token,
                description='Payment for Order #{}'.format(order.id),
            )

            transaction_details = {
                'charge_id': charge.id,
                'payment_status': charge.status,
            }

            Payment.objects.create(
                order=order,
                payment_method='stripe',
                transaction_details=transaction_details,
                status='success',
                user=self.request.user,
                stripe_token=stripe_token
            )

        except stripe.error.StripeError as e:
            # Handle Stripe errors
            return Response({'detail': 'Payment failed. {}'.format(str(e))}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            # Handle value error for invalid amount
            return Response({'detail': 'Invalid amount value. {}'.format(str(e))}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Handle other exceptions
            return Response({'detail': 'An unexpected error occurred. {}'.format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def clear_cart(self, cart):
        cart.cart_items.all().delete()

    def update_shipping_status(self, order):
        order.is_shipped = True
        order.shipping_date = timezone.now()
        order.save()

    def perform_create(self, serializer):
        cart_id = serializer.validated_data['cart_id']
        stripe_token = serializer.validated_data['stripe_token']

        cart = self.get_cart(cart_id)
        order = self.create_order(cart)

        try:
            self.process_payment(order, stripe_token)
            self.clear_cart(cart)
            self.update_shipping_status(order)

            # Print statements for debugging
            print("Payment successful and products shipped.")
            print(f"Order ID: {order.id}")
            print(f"Amount Paid: {order.amount}")
            print(f"Charge ID: {order.payment.transaction_details.get('charge_id', '')}")
            print(f"Payment Status: {order.payment.transaction_details.get('payment_status', '')}")
            print(f"Shipping Date: {order.shipping_date}")

            # Return a detailed response for testing
            return Response({
                'detail': 'Payment successful and products shipped.',
                'order_id': order.id,
                'amount_paid': order.amount,
                'charge_id': order.payment.transaction_details.get('charge_id', ''),
                'payment_status': order.payment.transaction_details.get('payment_status', ''),
                'shipping_date': order.shipping_date,
            }, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            # Print statements for debugging
            print(f"StripeError: {str(e)}")

            # Handle Stripe errors
            return Response({'detail': 'Payment failed. {}'.format(str(e))}, status=status.HTTP_400_BAD_REQUEST)

        except ValueError as e:
            # Print statements for debugging
            print(f"ValueError: {str(e)}")

            # Handle value error for invalid amount
            return Response({'detail': 'Invalid amount value. {}'.format(str(e))}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Print statements for debugging
            print(f"Unexpected Error: {str(e)}")

            # Handle other exceptions
            return Response({'detail': 'An unexpected error occurred. {}'.format(str(e))}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentDetailView(RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Check if the user is authenticated
        if user.is_authenticated:
            return Payment.objects.filter(order__user=user)
        else:
            # Handle the case where the user is not authenticated
            return Payment.objects.none()

class PaymentListView(ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Check if the user is authenticated and not an AnonymousUser
        if user.is_authenticated and not isinstance(user, AnonymousUser):
            return Payment.objects.filter(user=user)
        else:
            # Handle the case where the user is not authenticated or is AnonymousUser
            return Payment.objects.none()

#------------------------------------------------------------------------------------------------------

class ReviewListView(ListAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

class ReviewCreateView(CreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Automatically set the user based on the authenticated user
        serializer.save(user=self.request.user)
        
#----------------------------------------------------------------------------------------------------------


# class AddressListView(ListAPIView):
#     queryset = Address.objects.all()
#     serializer_class = AddressSerializer

#     def get_queryset(self):
#         return Address.objects.filter(user=self.request.user)

# class AddressDetailView(RetrieveAPIView):
#     queryset = Address.objects.all()
#     serializer_class = AddressSerializer

#     def get_queryset(self):
#         return Address.objects.filter(user=self.request.user)

# class AddressCreateView(CreateAPIView):
#     queryset = Address.objects.all()
#     serializer_class = AddressSerializer

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

# class AddressUpdateView(UpdateAPIView):
#     queryset = Address.objects.all()
#     serializer_class = AddressSerializer

#     def get_queryset(self):
#         return Address.objects.filter(user=self.request.user)

# class AddressDeleteView(DestroyAPIView):
#     queryset = Address.objects.all()
#     serializer_class = AddressSerializer

#     def get_queryset(self):
#         return Address.objects.filter(user=self.request.user)
    

#-----------------------------------------------------------------------------------------------------------
    
    
# class CouponListView(ListAPIView):
#     queryset = Coupon.objects.all()
#     serializer_class = CouponSerializer

#     def get_queryset(self):
#         return Coupon.objects.filter(user=self.request.user)

# class CouponDetailView(RetrieveAPIView):
#     queryset = Coupon.objects.all()
#     serializer_class = CouponSerializer

#     def get_queryset(self):
#         return Coupon.objects.filter(user=self.request.user)



#--------------------------------------------------------------------------------------------------------

class WishlistViewSet(ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        #it sets the user based on the user making the request
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_product(self, request, pk=None):
        wishlist = self.get_object()
        product_id = request.data.get('product_id')

        product = get_object_or_404(Product, pk=product_id)

        wishlist.add_product(product)
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_product(self, request, pk=None):
        wishlist = self.get_object()
        product_id = request.data.get('product_id')

        product = get_object_or_404(Product, pk=product_id)

        wishlist.remove_product(product)
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def list_products(self, request, pk=None): 
        wishlist = self.get_object()
        serializer = ProductSerializer(wishlist.products.all(), many=True)
        return Response(serializer.data)


#------------------------------------------------------------------------------------------------------

# class ShippingListView(ListAPIView):
#     queryset = Shipping.objects.all()
#     serializer_class = ShippingSerializer

#     def get_queryset(self):
#         return Shipping.objects.filter(user=self.request.user)

# class ShippingDetailView(RetrieveAPIView):
#     queryset = Shipping.objects.all()
#     serializer_class = ShippingSerializer

#     def get_queryset(self):
#         return Shipping.objects.filter(user=self.request.user)

#---------------------------------------------------------------------------------------------------------

# class NotificationListView(ListAPIView):
#     queryset = Notification.objects.all()
#     serializer_class = NotificationSerializer

#     def get_queryset(self):
#         return Notification.objects.filter(user=self.request.user)

# class NotificationDetailView(RetrieveAPIView):
#     queryset = Notification.objects.all()
#     serializer_class = NotificationSerializer

#     def get_queryset(self):
#         return Notification.objects.filter(user=self.request.user)

# class NotificationMarkAsReadView(UpdateAPIView):
#     queryset = Notification.objects.all()
#     serializer_class = NotificationSerializer

#     def get_queryset(self):
#         return Notification.objects.filter(user=self.request.user)

# class NotificationMarkAllAsReadView(APIView):
#     def post(self, request, *args, **kwargs):
#         notifications = Notification.objects.filter(user=self.request.user, is_read=False)
#         notifications.update(is_read=True)
#         return Response({'message': 'All notifications marked as read'}, status=status.HTTP_200_OK)    


#---------------------------------------------------------------------------------------------------------

@method_decorator(csrf_exempt, name='dispatch')
class ContactView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.data)

        if form.is_valid():
            # Process the valid form data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message = form.cleaned_data['message']

            # Save the message to the database
            ContactMessage.objects.create(name=name, email=email, message=message)

            return Response({'success': True})
        else:
            return Response({'error': 'Invalid form data'})
   
    



    

    
    
    