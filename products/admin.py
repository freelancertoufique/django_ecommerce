from django.contrib import admin
from products.models import (
    Product,
    Category,
    Cart,
    CartItem,
    ProductVariant,
    Wishlist,
    ProductImage
)

admin.site.register(Product)
admin.site.register(ProductVariant)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Wishlist)
admin.site.register(ProductImage)

