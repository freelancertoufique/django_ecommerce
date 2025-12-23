from django.shortcuts import redirect, render
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views import View

from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Customer, ResetPassword as ResetPassModel
from django.core.mail import send_mail


class RegisterView(View):
    """Handle customer registration"""

    def post(self, request):
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        redirect_url = 'index'

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
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
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

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
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


class SendResetEamil(View):
    def get(self, request):
        return render(request, 'ecommerce/send_reset.html')

    def post(self, request):
        email = request.POST.get("email")

        users = User.objects.filter(email=email)
        if not users.exists():
            messages.error(request, 'Email not found!!!')
            return render(request, 'ecommerce/send_reset.html')

        token_obj = ResetPassModel.objects.create(user=users.first())

        send_mail(
            'Reset Password',
            f'Here is your password reset url: http://localhost:8000/customers/reset-password/{token_obj.token}/',
            'r.rahul.devops007@gmail.com',
            [email],
            fail_silently=False,
        )

        return redirect('send_reset')


class ResetPassword(View):
    def get(self, request, token):
        try:
            reset_token = ResetPassModel.objects.get(token=token)
            if not reset_token.is_valid():
                messages.error(request, 'This reset link has expired or been used.')
                return redirect('send_reset')
            return render(request, 'ecommerce/reset-pass.html', {'token': token})
        except ResetPassModel.DoesNotExist:
            messages.error(request, 'Invalid reset link.')

        return render(request, 'ecommerce/reset-pass.html')

    def post(self, request, token):
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not password or not confirm_password:
            messages.error(request, 'Both password fields are required.')
            return redirect('reset_password', token=token)

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('reset_password', token=token)

        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect('reset_password', token=token)

        try:
            reset_token = ResetPassModel.objects.get(token=token)
            if not reset_token.is_valid():
                messages.error(request, 'This reset link has expired or been used.')
                return redirect('send_reset')

            # Update password
            user = reset_token.user
            user.set_password(password)
            user.save()

            # Mark token as used
            reset_token.is_used = True
            reset_token.save()

            messages.success(request, 'Password reset successful. Please login.')
            return redirect('index')
        except ResetPassModel.DoesNotExist:
            messages.error(request, 'Invalid reset link.')
            return redirect('send_reset')
