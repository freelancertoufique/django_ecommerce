import uuid
from django.conf import settings
from sslcommerz_lib import SSLCOMMERZ


class SSLCommerzService:
    def __init__(self):
        self.settings = {
            'store_id': settings.SSLCOMMERZ_STORE_ID,
            'store_pass': settings.SSLCOMMERZ_STORE_PASS,
            'issandbox': settings.SSLCOMMERZ_IS_SANDBOX,
        }
        self.sslcz = SSLCOMMERZ(self.settings)

    def generate_tran_id(self):
        return f"TXN-{uuid.uuid4().hex[:16].upper()}"

    def create_payment_session(self, order, customer, address):
        tran_id = self.generate_tran_id()

        post_body = {
            'total_amount': float(order.total),
            'currency': 'BDT',
            'tran_id': tran_id,
            'success_url': settings.SSLCOMMERZ_SUCCESS_URL,
            'fail_url': settings.SSLCOMMERZ_FAIL_URL,
            'cancel_url': settings.SSLCOMMERZ_CANCEL_URL,
            'ipn_url': settings.SSLCOMMERZ_IPN_URL,
            'emi_option': 0,
            'cus_name': address.full_name or 'Guest',
            'cus_email': (
                customer.user.email if customer else 'guest@example.com'
            ),
            'cus_phone': address.phone or '01700000000',
            'cus_add1': address.address_line1,
            'cus_add2': address.address_line2 or '',
            'cus_city': address.city or 'Dhaka',
            'cus_state': address.state or '',
            'cus_postcode': address.postal_code or '',
            'cus_country': address.country or 'Bangladesh',
            'shipping_method': 'YES',
            'ship_name': address.full_name or 'Guest',
            'ship_add1': address.address_line1,
            'ship_add2': address.address_line2 or '',
            'ship_city': address.city or 'Dhaka',
            'ship_state': address.state or '',
            'ship_postcode': address.postal_code or '',
            'ship_country': address.country or 'Bangladesh',
            'num_of_item': order.items.count(),
            'product_name': 'Order Items',
            'product_category': 'General',
            'product_profile': 'general',
        }

        response = self.sslcz.createSession(post_body)
        return tran_id, response

    def validate_transaction(self, val_id):
        return self.sslcz.validationTransactionOrder(val_id)

    def validate_ipn(self, post_data):
        return self.sslcz.hash_validate_ipn(post_data)
