from django.contrib import admin

# Register your models here.

from orders.models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    search_fields = ['variant__sku', 'variant__product__name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'customer',
        'session_id',
        'status',
        'subtotal',
        'total',
        'created_at',
    ]
    list_filter = ['status', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'variant',
        'quantity',
        'unit_price',
        'created_at',
    ]
    list_filter = ['created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'order',
        'payment_type',
        'status',
        'amount',
        'transaction_id',
        'created_at',
    ]
    list_filter = ['payment_type', 'status', 'created_at', 'updated_at']
    search_fields = ['order__id', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
