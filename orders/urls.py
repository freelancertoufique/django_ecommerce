from django.urls import path
from orders.views import (
    SSLCommerzSuccessView,
    SSLCommerzFailView,
    SSLCommerzCancelView,
    SSLCommerzIPNView,
)

urlpatterns = [
    path(
        'sslcommerz/success/',
        SSLCommerzSuccessView.as_view(),
        name='sslcommerz_success'
    ),
    path(
        'sslcommerz/fail/',
        SSLCommerzFailView.as_view(),
        name='sslcommerz_fail'
    ),
    path(
        'sslcommerz/cancel/',
        SSLCommerzCancelView.as_view(),
        name='sslcommerz_cancel'
    ),
    path(
        'sslcommerz/ipn/',
        SSLCommerzIPNView.as_view(),
        name='sslcommerz_ipn'
    ),
]
