import datetime
import uuid
from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer'
    )
    test_field = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user.first_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'


class ResetPassword(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name='password_token'
    )
    token = models.CharField(max_length=120, default=uuid.uuid4)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token

    def is_valid(self):
        if self.is_used:
            return False
        exp_time = self.created_at + datetime.timedelta(hours=1)
        if self.created_at < exp_time:
            return True

        return False


class Address(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        related_name='addresses',
        blank=True,
        null=True
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        related_name='addresses',
        blank=True,
        null=True
    )
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.customer:
            return f"{self.customer} - {self.address_line1}"
        return self.address_line1
