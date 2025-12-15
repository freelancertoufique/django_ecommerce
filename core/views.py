from django.shortcuts import render
from django.views import View
from customers.models import Customer
from products.models import Category


class IndexView(View):
    def get(self, request):
        # customer = None
        # if request.user.is_authenticated:
        #     print("email", request.user.id)
        #     customer = Customer.objects.get(user=request.user)
        # context = {
        #     "customer": customer
        # }
        return render(request, 'ecommerce/index.html')
