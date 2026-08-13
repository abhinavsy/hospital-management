from django.urls import path

from .views import (
    CreatePaytmPaymentView,
    PaytmCallbackView,
    VerifyPaytmPaymentView,
)

urlpatterns = [
    path(
        "create/",
        CreatePaytmPaymentView.as_view(),
        name="create-payment",
    ),
    path(
        "verify/",
        VerifyPaytmPaymentView.as_view(),
        name="verify-payment",
    ),
    path(
        "paytm/callback/",
        PaytmCallbackView.as_view(),
        name="paytm-callback",
    ),
]
