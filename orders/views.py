from django.shortcuts import redirect, render
from django.contrib import messages
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from decimal import Decimal

from orders.models import Order, Payment
from orders.sslcommerz_service import SSLCommerzService


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzSuccessView(View):
    def post(self, request):
        tran_id = request.POST.get('tran_id')
        val_id = request.POST.get('val_id')
        card_type = request.POST.get('card_type')
        card_brand = request.POST.get('card_brand')
        bank_tran_id = request.POST.get('bank_tran_id')

        if not tran_id or not val_id:
            messages.error(request, 'Invalid payment response.')
            return redirect('cart')

        try:
            payment = Payment.objects.get(tran_id=tran_id)
        except Payment.DoesNotExist:
            messages.error(request, 'Payment not found.')
            return redirect('cart')

        if payment.status == Payment.Status.PAID:
            context = {
                'order': payment.order,
                'payment': payment,
            }
            return render(request, 'sslcommerz/success.html', context)

        sslcz_service = SSLCommerzService()
        validation_response = sslcz_service.validate_transaction(val_id)

        if (
            validation_response.get('status') == 'VALID'
            and Decimal(validation_response.get('amount', 0)) == payment.amount
            and validation_response.get('tran_id') == tran_id
        ):
            payment.status = Payment.Status.PAID
            payment.val_id = val_id
            payment.bank_tran_id = bank_tran_id
            payment.card_type = card_type
            payment.card_brand = card_brand
            payment.transaction_id = bank_tran_id
            payment.save()

            order = payment.order
            order.status = Order.Status.CONFIRMED
            order.save()

            context = {
                'order': order,
                'payment': payment,
            }
            return render(request, 'sslcommerz/success.html', context)
        else:
            payment.status = Payment.Status.FAILED
            payment.save()
            messages.error(request, 'Payment validation failed.')
            return redirect('cart')


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzFailView(View):
    def post(self, request):
        tran_id = request.POST.get('tran_id')

        if tran_id:
            try:
                payment = Payment.objects.get(tran_id=tran_id)
                payment.status = Payment.Status.FAILED
                payment.save()
                payment.order.status = "canceled"
                payment.order.save()
            except Payment.DoesNotExist:
                pass

        return render(request, 'sslcommerz/fail.html')


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzCancelView(View):
    def post(self, request):
        tran_id = request.POST.get('tran_id')

        if tran_id:
            try:
                payment = Payment.objects.get(tran_id=tran_id)
                payment.status = Payment.Status.CANCELED
                payment.save()
            except Payment.DoesNotExist:
                pass

        return render(request, 'sslcommerz/cancel.html')


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzIPNView(View):
    def post(self, request):
        tran_id = request.POST.get('tran_id')
        val_id = request.POST.get('val_id')

        if not tran_id or not val_id:
            return HttpResponse('Invalid IPN', status=400)

        try:
            payment = Payment.objects.get(tran_id=tran_id)
        except Payment.DoesNotExist:
            return HttpResponse('Payment not found', status=404)

        if payment.status == Payment.Status.PAID:
            return HttpResponse('Already processed', status=200)

        sslcz_service = SSLCommerzService()

        if not sslcz_service.validate_ipn(request.POST.dict()):
            return HttpResponse('Hash validation failed', status=400)

        validation_response = sslcz_service.validate_transaction(val_id)

        if (
            validation_response.get('status') == 'VALID'
            and Decimal(validation_response.get('amount', 0)) == payment.amount
            and validation_response.get('tran_id') == tran_id
        ):
            payment.status = Payment.Status.PAID
            payment.val_id = val_id
            payment.bank_tran_id = request.POST.get('bank_tran_id')
            payment.card_type = request.POST.get('card_type')
            payment.card_brand = request.POST.get('card_brand')
            payment.transaction_id = request.POST.get('bank_tran_id')
            payment.save()

            order = payment.order
            order.status = Order.Status.CONFIRMED
            order.save()

            return HttpResponse('IPN processed successfully', status=200)
        else:
            payment.status = Payment.Status.FAILED
            payment.save()
            return HttpResponse('Validation failed', status=400)
