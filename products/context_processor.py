from products.models import Category, Cart, Wishlist


def category_context(request):
    categories = Category.objects.filter(
        is_active=True, parent__isnull=True
    )
    return {
        'main_menu': categories,
    }


def cart_context(request):
    """Add cart data to template context.

    Standard e-commerce cart handling:
    - Authenticated customers: Cart tied to user account
    - Anonymous users: Cart tied to session ID
    - Admin/Staff users: No cart (they don't shop)
    - Prevents null session_id by forcing session creation
    """
    cart_items_count = 0
    cart_total = 0
    cart = None

    if request.user.is_authenticated:
        # Skip cart creation for admin/staff users
        if not (request.user.is_staff or request.user.is_superuser):
            # Regular authenticated customers: cart tied to user account
            cart, created = Cart.objects.get_or_create(
                customer__user=request.user
            )
            cart_items_count = cart.total_items
            cart_total = cart.total_price
    else:
        # Anonymous users: cart tied to session
        # Force session creation if it doesn't exist (prevents null session_id)
        if not request.session.session_key:
            request.session.create()

        # Now safely create/get cart with valid session_id
        cart, created = Cart.objects.get_or_create(
            session_id=request.session.session_key
        )
        cart_items_count = cart.total_items
        cart_total = cart.total_price

    return {
        'header_cart': cart,
        'header_cart_items_count': cart_items_count,
        'header_cart_total': cart_total,
    }


def wishlist_context(request):
    """Add wishlist count to template context."""
    wishlist_count = 0

    # Only show wishlist for regular customers, not admin/staff
    if request.user.is_authenticated:
        if not (request.user.is_staff or request.user.is_superuser):
            wishlist_count = Wishlist.objects.filter(
                customer__user=request.user
            ).count()

    return {
        'header_wishlist_count': wishlist_count,
    }
