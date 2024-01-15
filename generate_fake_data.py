import os
import django
from faker import Faker
from django.conf import settings
from django.apps import apps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django.setup()

from ecommerce_app.models import Product, Order, Cart, CartItem, Payment, Review, Address, Coupon, Wishlist, Shipping, Notification
from django.contrib.auth.models import User

fake = Faker()

def generate_fake_data():
    # Create Users
    users = []
    for _ in range(50):
        users.append(User.objects.create(username=fake.user_name(), email=fake.email()))

    # Create Products
    products = []
    for _ in range(50):
        products.append(Product.objects.create(
            name=fake.word(),
            description=fake.sentence(),
            price=fake.random_int(min=10, max=100),
            stock_quantity=fake.random_int(min=1, max=100),
            user=User.objects.order_by('?').first()
        ))

    # Create Carts with CartItems
    carts = []
    cart_items = []
    for _ in range(10):
        user = User.objects.order_by('?').first()

        # Check if a Cart already exists for the user
        cart, created = Cart.objects.get_or_create(user=user)

        # If a Cart already exists, skip creating a new one
        if not created:
            continue

        carts.append(cart)

    products = Product.objects.order_by('?')[:3]
    for product in products:
        cart_items.append(CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=fake.random_int(min=1, max=5)
        ))


    # Create Orders with Products
    orders = []
    for _ in range(20):
        user = User.objects.order_by('?').first()
        order = Order.objects.create(amount=fake.random_int(min=50, max=500), user=user)
        products = Product.objects.order_by('?')[:3]
        order.products.set(products)
        orders.append(order)

    # Create Payments with unique order_id
    payments = []
    for order in orders:
        payments.append(Payment.objects.create(
            order=order,
            payment_method=fake.word(),
            transaction_details=fake.text(),
            status=fake.random_element(elements=('Pending', 'Success', 'Failed')),
            user=order.user
        ))

    # Create Reviews
    reviews = []
    for _ in range(40):
        user = User.objects.order_by('?').first()
        product = Product.objects.order_by('?').first()
        reviews.append(Review.objects.create(
            user=user,
            product=product,
            content=fake.text(),
            rating=fake.random_int(min=1, max=5)
        ))

    # Create Addresses
    addresses = []
    for _ in range(25):
        user = User.objects.order_by('?').first()
        addresses.append(Address.objects.create(
            user=user,
            street_address=fake.street_address(),
            city=fake.city(),
            state=fake.state(),
            zip_code=fake.zipcode(),
            is_default_shipping=fake.boolean(),
            is_default_billing=fake.boolean()
        ))

    # Create Coupons
    coupons = []
    for _ in range(10):
        coupons.append(Coupon.objects.create(
            code=fake.uuid4(),
            discount_amount=fake.random_int(min=5, max=20),
            expiration_date=fake.future_date(end_date="+30d"),
            user=User.objects.order_by('?').first()
        ))

    # Create Wishlists with Products
    wishlists = []
    for _ in range(15):
        user = User.objects.order_by('?').first()
        wishlist = Wishlist.objects.create(user=user)
        wishlists.append(wishlist)

        products = Product.objects.order_by('?')[:3]
        wishlist.products.set(products)

    # Create Shipping Methods
    shippings = []
    for _ in range(8):
        shippings.append(Shipping.objects.create(
            provider_name=fake.company(),
            method_name=fake.word(),
            cost=fake.random_int(min=5, max=30),
            user=User.objects.order_by('?').first()
        ))

    # Create Notifications
    notifications = []
    for _ in range(20):
        user = User.objects.order_by('?').first()
        notifications.append(Notification.objects.create(
            user=user,
            message=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            is_read=fake.boolean()
        ))

if __name__ == "__main__":
    generate_fake_data()
