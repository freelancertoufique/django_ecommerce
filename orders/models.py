from django.db import models
import uuid

# Create your models here.

from customers.models import Customer
from products.models import ProductVariant


def create_transaction_id():
    return str(uuid.uuid4().hex[:20])


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'
        CANCELED = 'canceled', 'Canceled'

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='orders'
    )
    session_id = models.CharField(max_length=512, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['order', 'variant']

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"OrderItem #{self.pk} (Order #{self.order_id})"


class Payment(models.Model):
    class PaymentType(models.TextChoices):
        SSLCOMMERZ = 'sslcommerz', 'SSLCommerz'
        COD = 'cod', 'Cash On Delivery'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        CANCELED = 'canceled', 'Canceled'

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transaction_id = models.CharField(max_length=255, blank=True, null=True, default=create_transaction_id)
    tran_id = models.CharField(
        max_length=255, blank=True, null=True, unique=True
    )
    val_id = models.CharField(max_length=255, blank=True, null=True)
    bank_tran_id = models.CharField(max_length=255, blank=True, null=True)
    card_type = models.CharField(max_length=100, blank=True, null=True)
    card_brand = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment #{self.pk} (Order #{self.order_id})"
