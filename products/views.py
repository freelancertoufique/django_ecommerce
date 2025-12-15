from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.views.generic import ListView, DetailView

from products.models import Product, Cart, CartItem, ProductVariant

from products.models import Category
from customers.models import Customer


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
        return render(request, 'ecommerce/cart.html', {})


class WishlistView(View):
    def get(self, request):
        return render(request, 'ecommerce/wishlist.html')


class CheckoutView(View):
    def get(self, request):
        return render(request, 'ecommerce/checkout.html')


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
