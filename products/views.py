from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.db import transaction

from products.models import Product, Cart, CartItem, ProductVariant

from products.models import Category
from customers.models import Customer
from customers.models import Address
from orders.models import Order, OrderItem, Payment
from orders.sslcommerz_service import SSLCommerzService


class ProductListView(ListView):
    model = Product
    template_name = 'ecommerce/category.html'
    context_object_name = 'products'
    paginate_by = 3

    def get_queryset(self):
        category_slug = self.request.GET.get("category")
        if category_slug:
            qs = Product.objects.filter(is_active=True, category__slug=category_slug).select_related('category').order_by('-created_at')
        else:
            qs = Product.objects.filter(is_active=True).select_related('category').order_by('-created_at')
        return qs


class ProductDetailView(DetailView):
    model = Product
    template_name = 'ecommerce/product.html'
    context_object_name = 'product'


class CartView(View):
    def get(self, request):
        cart = None
        items = []

        if request.user.is_authenticated and not (
            request.user.is_staff or request.user.is_superuser
        ):
            customer, _ = Customer.objects.get_or_create(user=request.user)
            cart = Cart.objects.filter(customer=customer).first()
        else:
            if not request.session.session_key:
                request.session.create()
            cart = Cart.objects.filter(
                session_id=request.session.session_key
            ).first()

        if cart:
            items = (
                cart.items.select_related('variant', 'variant__product')
                .all()
            )

        context = {
            'cart': cart,
            'items': items,
            'cart_subtotal': cart.total_price if cart else 0,
            'cart_total_items': cart.total_items if cart else 0,
        }
        return render(request, 'ecommerce/cart.html', context)


class WishlistView(View):
    def get(self, request):
        return render(request, 'ecommerce/wishlist.html')


class CheckoutView(View):
    def get(self, request):
        address = None
        if request.user.is_authenticated and not (
            request.user.is_staff or request.user.is_superuser
        ):
            customer, _ = Customer.objects.get_or_create(user=request.user)
            address = customer.addresses.order_by('-updated_at').first()

        context = {
            'address': address,
            'selected_payment_type': request.session.get('payment_type'),
        }
        return render(request, 'ecommerce/checkout.html', context)

    def post(self, request):
        payment_type = request.POST.get('payment_type')
        if payment_type not in ('sslcommerz', 'cod'):
            messages.error(request, 'Please select a payment method.')
            return redirect('checkout')

        cart = None
        cart_items = []
        if request.user.is_authenticated and not (
            request.user.is_staff or request.user.is_superuser
        ):
            customer, _ = Customer.objects.get_or_create(user=request.user)
            cart = Cart.objects.filter(customer=customer).first()
        else:
            customer = None
            if not request.session.session_key:
                request.session.create()
            cart = Cart.objects.filter(
                session_id=request.session.session_key
            ).first()

        if cart:
            cart_items = list(
                cart.items.select_related('variant', 'variant__product').all()
            )

        if not cart_items:
            messages.error(request, 'Your cart is empty.')
            return redirect('cart')

        first_name = (request.POST.get('first_name') or '').strip()
        last_name = (request.POST.get('last_name') or '').strip()
        full_name = (f"{first_name} {last_name}").strip() or None

        phone = (request.POST.get('phone') or '').strip() or None
        address_line1 = (request.POST.get('address_line1') or '').strip()
        address_line2 = (
            request.POST.get('address_line2') or ''
        ).strip() or None
        city = (request.POST.get('city') or '').strip() or None
        state = (request.POST.get('state') or '').strip() or None
        postal_code = (request.POST.get('postal_code') or '').strip() or None
        country = (request.POST.get('country') or '').strip() or None

        if not address_line1:
            messages.error(request, 'Street address is required.')
            return redirect('checkout')

        customer = None
        address = None
        if request.user.is_authenticated and not (
            request.user.is_staff or request.user.is_superuser
        ):
            customer, _ = Customer.objects.get_or_create(user=request.user)
            address = customer.addresses.order_by('-updated_at').first()

        if address is None:
            address = Address.objects.create(
                customer=customer,
                address_line1=address_line1,
            )

        address.customer = customer
        address.full_name = full_name
        address.phone = phone
        address.address_line1 = address_line1
        address.address_line2 = address_line2
        address.city = city
        address.state = state
        address.postal_code = postal_code
        address.country = country
        address.save()

        with transaction.atomic():
            order_subtotal = sum((item.subtotal for item in cart_items), 0)
            order = Order.objects.create(
                customer=customer,
                session_id=(
                    request.session.session_key if not customer else None
                ),
                subtotal=order_subtotal,
                total=order_subtotal,
                status=Order.Status.PENDING,
            )

            for item in cart_items:
                if not item.variant:
                    continue
                OrderItem.objects.create(
                    order=order,
                    variant=item.variant,
                    quantity=item.quantity,
                    unit_price=item.variant.product.current_price,
                )

            payment = Payment.objects.create(
                order=order,
                payment_type=payment_type,
                amount=order.total,
                status=Payment.Status.PENDING,
            )

            address.order = order
            address.save(update_fields=['order', 'updated_at'])

            if payment_type == 'sslcommerz':
                try:
                    sslcz_service = SSLCommerzService()
                    tran_id, response = sslcz_service.create_payment_session(
                        order, customer, address
                    )

                    payment.tran_id = tran_id
                    payment.save(update_fields=['tran_id'])

                    if response.get('status') == 'SUCCESS':
                        gateway_url = response.get('GatewayPageURL')
                        if gateway_url:
                            return redirect(gateway_url)
                        else:
                            messages.error(
                                request,
                                'Payment gateway URL not found.'
                            )
                            return redirect('cart')
                    else:
                        messages.error(
                            request,
                            'Failed to initialize payment session.'
                        )
                        return redirect('cart')
                except Exception as e:
                    messages.error(
                        request,
                        f'Payment initialization error: {str(e)}'
                    )
                    return redirect('cart')
            else:
                cart.items.all().delete()
                request.session.pop('payment_type', None)
                messages.success(request, 'Order placed successfully.')
                return redirect('cart')


class AddToCartView(View):
    def post(self, request, product_id):
        redirect_url = request.META.get('HTTP_REFERER', 'product_list')

        product = get_object_or_404(Product, pk=product_id, is_active=True)
        variant_id = (
            request.POST.get('variant_id') or request.GET.get('variant_id')
        )
        size = (
            request.POST.get('size') or request.GET.get('size') or ''
        ).strip()
        color = (
            request.POST.get('color') or request.GET.get('color') or ''
        ).strip()
        quantity_raw = (
            request.POST.get('quantity') or request.GET.get('quantity')
        )

        try:
            quantity = int(quantity_raw) if quantity_raw else 1
        except ValueError:
            quantity = 1

        if quantity < 1:
            quantity = 1

        if variant_id:
            variant = get_object_or_404(
                ProductVariant,
                pk=variant_id,
                product=product,
                is_active=True,
            )
        else:
            variants = product.variants.filter(is_active=True)
            if size:
                variants = variants.filter(size=size)
            if color:
                variants = variants.filter(color=color)

            variant = variants.order_by('id').first()
            if not variant:
                if size or color:
                    messages.error(
                        request,
                        'Selected variant is not available for this product.'
                    )
                else:
                    messages.error(
                        request,
                        'No variant available for this product.'
                    )
                return redirect(redirect_url)

        if request.user.is_authenticated and not (
            request.user.is_staff or request.user.is_superuser
        ):
            customer, _ = Customer.objects.get_or_create(user=request.user)
            cart, _ = Cart.objects.get_or_create(customer=customer)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, _ = Cart.objects.get_or_create(
                session_id=request.session.session_key
            )

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant
        )
        if created:
            item.quantity = quantity
        else:
            item.quantity = item.quantity + quantity
        item.save(update_fields=['quantity', 'updated_at'])

        messages.success(request, 'Added to cart.')
        return redirect(redirect_url)

    def get(self, request, product_id):
        redirect_url = request.META.get('HTTP_REFERER')
        product = get_object_or_404(Product, pk=product_id, is_active=True)
        variant = ProductVariant.objects.filter(product=product).first()

        if request.user.is_authenticated and not (
            request.user.is_staff or request.user.is_superuser
        ):
            customer, _ = Customer.objects.get_or_create(user=request.user)
            cart, _ = Cart.objects.get_or_create(customer=customer)
        else:
            if not request.session.session_key:
                request.session.create()
            cart, _ = Cart.objects.get_or_create(
                session_id=request.session.session_key
            )
        _ = CartItem.objects.create(
            cart=cart,
            variant=variant,
            quantity=1
        )
        return redirect(redirect_url)
