from django.conf import settings
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import (
    StandardCheckoutPayRequest,
)
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient

from payment_app.utils import PaymentGateway

class PhonePeGateway(PaymentGateway):

    def __init__(self):

        if settings.IS_DEV == True:
            env = Env.SANDBOX
        else:
            env = Env.PRODUCTION

        self.client = StandardCheckoutClient.get_instance(
            client_id=settings.PHONEPE_CLIENT_ID,
            client_secret=settings.PHONEPE_CLIENT_SECRET,
            client_version=settings.PHONEPE_CLIENT_VERSION,
            env=env,
        )

    def create_payment(self, merchant_order_id, amount, patient_id):

        request = StandardCheckoutPayRequest.build_request(
            merchant_order_id=merchant_order_id,
            amount=amount,
            redirect_url=settings.PHONEPE_REDIRECT_URL,
        )

        response = self.client.pay(request)

        return response

    def verify_payment(self, payment_data):
        order_id = payment_data.get("order_id")

        return self.client.get_order_status(merchant_order_id=order_id)
