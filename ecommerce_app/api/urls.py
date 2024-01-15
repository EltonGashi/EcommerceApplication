from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ecommerce_app.api.views import (
    # Product Views
    ProductListView, ProductDetailView, ProductCreateView, ProductUpdateView, ProductDeleteView,
    
    # Order Views
    OrderListView, OrderDetailView, OrderCreateView, OrderUpdateView, OrderDeleteView,
    
    # Cart Views
    CartDetailView, CartAddProductView, CartRemoveProductView, CartUpdateProductQuantityView,
    
    # CartItem Views
    CartItemCreateView, CartItemUpdateView, CartItemDeleteView, CartItemListAPIView,
    
    # Payment Views
    PaymentProcessView, CartPaymentProcessView , PaymentDetailView, PaymentListView, 
    
    # Review Views
    ReviewListView, ReviewCreateView,
    
    # # Address Views
    # AddressListView, AddressDetailView, AddressCreateView, AddressUpdateView, AddressDeleteView,
    
    # # Coupon Views
    # CouponListView, CouponDetailView, 
    
    # # Wishlist Views
    WishlistViewSet,
    # WishlistListView, WishlistDetailView, WishlistAddProductView, WishlistRemoveProductView,
    
    # # Shipping Views
    # ShippingListView, ShippingDetailView,
    
    # # Notification Views
    # NotificationListView, NotificationDetailView, NotificationMarkAsReadView, NotificationMarkAllAsReadView,
    
    #Contact View
    ContactView,

)

router = DefaultRouter()
router.register(r'wishlist', WishlistViewSet, basename='wishlist')

urlpatterns = [
    # Product URLs
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/create/', ProductCreateView.as_view(), name='product-create'),
    path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),

    # Order URLs
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/create/', OrderCreateView.as_view(), name='order-create'),
    path('orders/<int:pk>/update/', OrderUpdateView.as_view(), name='order-update'),
    path('orders/<int:pk>/delete/', OrderDeleteView.as_view(), name='order-delete'),

    # Cart URLs
    path('cart/<int:pk>/', CartDetailView.as_view(), name='cart-detail'),
    path('cart/<int:pk>/remove/', CartRemoveProductView.as_view(), name='cart-remove-product'),
    path('cart/<int:pk>/update/', CartUpdateProductQuantityView.as_view(), name='cart-update-product-quantity'),
    path('cart/add/', CartAddProductView.as_view(), name='cart-add-product'),
    

    # CartItem URLs
    path('cartitem/create/', CartItemCreateView.as_view(), name='cartitem-create'),
    path('cartitem/<int:pk>/update/', CartItemUpdateView.as_view(), name='cartitem-update'),
    path('cartitem/<int:pk>/delete/', CartItemDeleteView.as_view(), name='cartitem-delete'),
    path('cart/items/', CartItemListAPIView.as_view(), name='cart-items-list'),

    # Payment URLs
    path('payment/process/', PaymentProcessView.as_view(), name='payment-process'),
    path('payment/cart/process/', CartPaymentProcessView.as_view(), name='payment-cart-process'),
    path('payment/<int:pk>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/', PaymentListView.as_view(), name='payment-list'),

    # Review URLs
    path('reviews/', ReviewListView.as_view(), name='review-list'),
    path('reviews/create/', ReviewCreateView.as_view(), name='review-create'),

    # # Address URLs
    # path('addresses/', AddressListView.as_view(), name='address-list'),
    # path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
    # path('addresses/create/', AddressCreateView.as_view(), name='address-create'),
    # path('addresses/<int:pk>/update/', AddressUpdateView.as_view(), name='address-update'),
    # path('addresses/<int:pk>/delete/', AddressDeleteView.as_view(), name='address-delete'),

    # # Coupon URLs
    # path('coupons/', CouponListView.as_view(), name='coupon-list'),
    # path('coupons/<int:pk>/', CouponDetailView.as_view(), name='coupon-detail'),
    # # path('coupons/apply/', CouponApplyView.as_view(), name='coupon-apply'),

    # # Wishlist URLs
    path('', include(router.urls)),
    path('wishlist/<int:pk>/remove_product/', WishlistViewSet.as_view({'get': 'remove_product'}), name='wishlist-remove-products'),
    path('wishlist/<int:pk>/list_products/', WishlistViewSet.as_view({'get': 'list_products'}), name='wishlist-list-products'),
    # path('wishlist/', WishlistListView.as_view(), name='wishlist-list'),
    # path('wishlist/<int:pk>/', WishlistDetailView.as_view(), name='wishlist-detail'),
    # path('wishlist/add/', WishlistAddProductView.as_view(), name='wishlist-add-product'),
    # path('wishlist/<int:pk>/remove/', WishlistRemoveProductView.as_view(), name='wishlist-remove-product'),

    # # Shipping URLs
    # path('shipping/', ShippingListView.as_view(), name='shipping-list'),
    # path('shipping/<int:pk>/', ShippingDetailView.as_view(), name='shipping-detail'),

    # # Notification URLs
    # path('notifications/', NotificationListView.as_view(), name='notification-list'),
    # path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    # path('notifications/<int:pk>/mark-as-read/', NotificationMarkAsReadView.as_view(), name='notification-mark-as-read'),
    # path('notifications/mark-all-as-read/', NotificationMarkAllAsReadView.as_view(), name='notification-mark-all-as-read'),
    
    
    # Contact URLs
    path('contact/', ContactView.as_view(), name='contact_view'),
]
