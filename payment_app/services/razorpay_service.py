import razorpay
from django.conf import settings
from payment_app.utils import PaymentGateway


class RazorPayPayment(PaymentGateway):
    """Razorpay Payment class"""

    def __init__(self):

        key_id = settings.RAZORPAY_CLIENT_ID
        secret_key = settings.RAZORPAY_SECRET_KEY
        self.client = razorpay.Client(auth=(key_id, secret_key))

    def create_payment_order(self, amount, currency, order_id, patient_id):
        """Create razorpay order"""
        client = self.client
        data = {
            "amount": amount,
            "currency": currency,
            "receipt": order_id,
        }
        order = client.order.create(data)
        razorpay_order_id = order["id"]
        return razorpay_order_id

    def verify_payment(self, payment_data):

        # verify signature
        result = self.client.utility.verify_payment_signature(payment_data)
        if result is not None:
            # Payment Success
            return True
        else:
            # Payment Failed
            return True
