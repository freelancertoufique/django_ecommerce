from django.shortcuts import redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Customer


class RegisterView(View):
    """Handle customer registration"""

    def post(self, request):
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        redirect_url = request.META.get('HTTP_REFERER', 'index')

        # Validation
        if not all([first_name, last_name, email, password]):
            messages.error(request, 'All fields are required.')
            return redirect(redirect_url)

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect(redirect_url)

        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create customer profile explicitly
        customer = Customer.objects.create(user=user)

        # Log the customer in
        login(request, user)
        messages.success(request, f'Welcome {customer}!')
        return redirect(redirect_url)


class LoginView(View):
    """Handle customer login"""

    def post(self, request):
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        redirect_url = request.META.get('HTTP_REFERER', 'index')

        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return redirect(redirect_url)

        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Check if user has a customer profile
            try:
                customer = user.customer
            except Customer.DoesNotExist:
                # Create customer if doesn't exist
                customer = Customer.objects.create(user=user)

            login(request, user)
            messages.success(request, f'Welcome back, {customer}!')
            return redirect(redirect_url)
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect(redirect_url)


class LogoutView(LoginRequiredMixin, View):
    """Handle customer logout"""
    login_url = 'login'

    def get(self, request):
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('index')
