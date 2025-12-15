from django.urls import path
from products.views import (
    ProductListView,
    ProductDetailView,
    CartView,
    WishlistView,
    CheckoutView,
    AddToCartView
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path(
        'product/<int:pk>/',
        ProductDetailView.as_view(),
        name='product_detail'
    ),
    path('cart/', CartView.as_view(), name='cart'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path(
        'cart/add/<int:product_id>/',
        AddToCartView.as_view(),
        name='add_to_cart'
    ),
]
