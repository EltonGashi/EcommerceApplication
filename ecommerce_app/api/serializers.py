from rest_framework import serializers
from django.db.models import Sum, F
from decimal import Decimal
from ecommerce_app.models import Product, Order, Cart, CartItem, Payment, Review, Wishlist

class ProductSerializer(serializers.ModelSerializer):
    initial_stock_quantity = serializers.IntegerField(write_only=True)

    class Meta:
        model = Product
        exclude = ('user',)

    def validate(self, data):
        # Ensure that required fields are present in the request
        required_fields = ['name', 'description', 'price','image', 'category']
        for field in required_fields:
            if field not in data:
                raise serializers.ValidationError(f"The '{field}' field is required.")
        
        # Additional custom validation logic if needed

        return data

    def create(self, validated_data):
        # Set the initial stock quantity when creating a new product
        initial_stock_quantity = validated_data.pop('initial_stock_quantity', 0)
        validated_data['stock_quantity'] = initial_stock_quantity

        return super().create(validated_data)
    

        
        
class OrderSerializer(serializers.ModelSerializer):
    products = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),  # Assuming 'product' is an integer ID
            required=True
        ),
        write_only=True
    )

    class Meta:
        model = Order
        exclude = ('user', 'amount')

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = super().create(validated_data)

        
        for product_data in products_data:
            product_id = product_data['product']
            quantity = product_data['quantity']
            order.products.add(Product.objects.get(pk=product_id), through_defaults={'quantity': quantity})

        # Calculate and update the order amount based on the added products
        order.amount = order.products.aggregate(total_amount=Sum(F('price')))['total_amount'] or Decimal(0)
        order.save()

        return order
        

        
class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'
        extra_kwargs = {'cart': {'required': False}}
        
        
class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = '__all__'
        
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['order', 'payment_method', 'transaction_details', 'status','stripe_token']

    stripe_token = serializers.CharField(write_only=True)
    
class CartPaymentSerializer(serializers.Serializer):
    cart_id = serializers.IntegerField()
    stripe_token = serializers.CharField(write_only=True)

    def validate_cart_id(self, value):
        # Check if the cart with the provided ID exists
        try:
            cart = Cart.objects.get(id=value)
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Invalid cart ID.")

        # Check if the cart belongs to the authenticated user
        if cart.user != self.context['request'].user:
            raise serializers.ValidationError("Invalid cart ID.")

        return value
        
        
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'user', 'product', 'content', 'rating']
        read_only_fields = ['user']  # Make 'user' read-only, as it will be set automatically
        
        
# class AddressSerializer(serializers.ModelSerializer):
    
#     class Meta:
#         model = Address
#         fields = '__all__'
        
        
# class CouponSerializer(serializers.ModelSerializer):
    
#     class Meta:
#         model = Coupon
#         fields = '__all__'
        
        
class WishlistSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Wishlist
        fields = '__all__'
        read_only_fields = ('user', )
        
        
# class ShippingSerializer(serializers.ModelSerializer):
    
#     class Meta:
#         model = Shipping
#         fields = '__all__'
        
        
# class NotificationSerializer(serializers.ModelSerializer):
    
#     class Meta:
#         model = Notification
#         fields = '__all__'
        

        
        