from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import stripe
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError



class Product(models.Model):
    name = models.CharField(max_length=25)
    description = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='products', null=True)
    image = models.ImageField(upload_to='', null=True, blank=True) 
    category = models.CharField(max_length=20, choices=[
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('books', 'Books'),

    ], null=True, blank=True)
    
    
    def get_reviews(self):
        return self.product_reviews.all()



class Order(models.Model):
    products = models.ManyToManyField(Product, related_name='orders')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)
    is_shipped = models.BooleanField(default=False)
    shipping_date = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    tracking_id = models.CharField(max_length=255, default=uuid.uuid4().hex, null=True, blank=True)
    status = models.CharField(max_length=50, default='pending')



class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('cart', 'product')

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=255)
    transaction_details = models.TextField()
    status = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    stripe_token = models.CharField(max_length=255, default='placeholder_value_for_existing_rows')
    
    def process_payment(self):
        # Check if the payment has already been processed
        if self.status != 'pending':
            return

        try:
            # Set your Stripe API key
            stripe.api_key = 'sk_test_51OUyI5AB7c17WEYMRRxRm8yzPacZzdeunwydgwZ2fEPnI44kgkpYvw0irY0DLse5ZdDlT60S8D7JZeB0raBK7Hm100HOWFGP5x'

            # Create a PaymentIntent to confirm the payment
            intent = stripe.PaymentIntent.create(
                amount=int(self.order.amount * 100),  # Convert amount to cents
                currency='usd',
                payment_method=self.stripe_token,
                confirmation_method='manual',
                confirm=True,
            )

            # Check the PaymentIntent status and update the Payment model accordingly
            if intent['status'] == 'succeeded':
                self.status = 'success'
            else:
                self.status = 'failed'
            
            # Update other relevant fields (e.g., transaction_details)
            self.transaction_details = f"PaymentIntent ID: {intent['id']}"

        except stripe.error.CardError as e:
            # Handle card errors (e.g., insufficient funds, expired card)
            self.status = 'failed'
            self.transaction_details = f"CardError: {str(e)}"

        except stripe.error.StripeError as e:
            # Handle other Stripe errors
            self.status = 'failed'
            self.transaction_details = f"StripeError: {str(e)}"

        except Exception as e:
            # Handle unexpected errors
            self.status = 'failed'
            self.transaction_details = f"UnexpectedError: {str(e)}"

        finally:
            # Save the changes to the Payment model
            self.save()
    
    
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_reviews')
    content = models.TextField()
    rating = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)])
    
    def clean(self):
        # Ensure that the rating is between 1 and 5
        if self.rating < 1 or self.rating > 5:
            raise ValidationError({'rating': 'Rating must be between 1 and 5.'})

# class Address(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
#     street_address = models.CharField(max_length=255)
#     city = models.CharField(max_length=255)
#     state = models.CharField(max_length=255)
#     zip_code = models.CharField(max_length=20)
#     is_default_shipping = models.BooleanField(default=False)
#     is_default_billing = models.BooleanField(default=False)

# class Coupon(models.Model):
#     code = models.CharField(max_length=20)
#     discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     expiration_date = models.DateField()
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupons')

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    products = models.ManyToManyField(Product, related_name='wishlist_products')

    def add_product(self, product):
        self.products.add(product)

    def remove_product(self, product):
        self.products.remove(product)

# class Shipping(models.Model):
#     provider_name = models.CharField(max_length=255)
#     method_name = models.CharField(max_length=255)
#     cost = models.DecimalField(max_digits=10, decimal_places=2)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shippings')

# class Notification(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
#     message = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)
#     is_read = models.BooleanField(default=False)



class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - {self.created_at}'