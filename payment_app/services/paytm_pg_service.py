from django.conf import settings
from paytmpg import (
    EChannelId,
    EnumCurrency,
    LibraryConstants,
    MerchantProperty,
    Money,
    Payment,
    PaymentDetailsBuilder,
    PaymentMode,
    PaymentStatusDetailBuilder,
    UserInfo,
)

from payment_app.utils import PaymentGateway

# Test Merchant ID
# GaafoA29764783892147
# Test Merchant Key
# viovZxi@tQAv2SWx
# Website
# WEBSTAGING
# Industry Type
# Retail
# Channel ID (For Website)
# WEB
# Channel ID (For Mobile Apps)
# WAP


class PaytmGateway(PaymentGateway):

    _initialized = False

    def __init__(self):
        self._initialize_paytm()

    @classmethod
    def _initialize_paytm(cls):

        if cls._initialized:
            return
        if settings.IS_DEV:
            enviornment = LibraryConstants.STAGING_ENVIRONMENT
        else:
            enviornment = LibraryConstants.STAGING_ENVIRONMENT

        MerchantProperty.set_callback_url(settings.PAYTM_CALLBACK_URL)
        MerchantProperty.initialize(
            enviornment,
            settings.PAYTM_MID,
            settings.PAYTM_MERCHANT_KEY,
            settings.PAYTM_CLIENT_ID,
            settings.PAYTM,
        )
        cls._initialized = True

    def create_payment_order(self, amount, currency, order_id, patient_id):

        txn_amount = Money(EnumCurrency.INR, str(amount))

        user_info = UserInfo()
        user_info.set_cust_id(patient_id)

        channel_id = EChannelId.WEB

        payment_details = PaymentDetailsBuilder(
            channel_id, order_id, txn_amount, user_info
        ).build()

        response = Payment.createTxnToken(payment_details)
        return response

    def verify_payment(self, payment_data):

        order_id = payment_data.get("order_id")
        read_timeout = 30 * 1000
        payment_status_detail = (
            PaymentStatusDetailBuilder(order_id).set_read_timeout(read_timeout).build()
        )
        response = Payment.getPaymentStatus(payment_status_detail)
        return response
