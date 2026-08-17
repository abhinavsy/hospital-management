# Create your views here.
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Patient, Payment
from payment_app.services.payment_service import PaymentService
from payment_app.services.paytm_pg_service import PaytmGateway
from payment_app.services.phonepe_service import PhonePeGateway


class CreatePaytmPaymentView(GenericAPIView):
    """
    Paytm payment gateway order create view
    """

    authentication_classes = []
    permission_classes = []
    serializer_class = None

    def post(self, request, pk):

        cust_object = self.get_object()
        gateway = PaytmGateway()
        service = PaymentService(gateway)
        serializer = self.get_serializer_class(data=request.data)
        if not serializer.is_valid():
            return Respone({"data": serializer.errors}, status.HTTP_400_BAD_REQUEST)
        amount = serializer.validated_data.get("amount")

        result = service.create_payment(
            cust_object.patient_id, amount=amount, currency=INR
        )
        return Response({"data": result})


class VerifyPaytmPaymentView(GenericAPIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request, pk):

        cust_object = self.get_object()
        gateway = PaytmGateway()
        service = PaymentService(gateway)
        payment_object = (
            Payment.objects.filter(
                is_paid=False, is_refunded=False, patient_id=cust_object
            )
            .order_by("-created_at")
            .first()
        )

        response = service.verify_payment({"order_id": payment_object.order_id})
        return Response(
            {
                "data": response,
            },
            status.HTTP_200_OK,
        )


class PaytmCallbackView(APIView):

    def post(self, request):

        order_id = request.POST.get("ORDERID")

        gateway = PaytmGateway()

        service = PaymentService(gateway)

        response = service.verify_payment({"order_id": order_id})
        return Response({"data": response})


class CreatePhonePeView(GenericAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = None

    def post(self, request, pk):

        customer_object = self.get_object()
        gateway = PhonePeGateway()
        service = PaymentService(gateway)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({"data": serializer.errors})

        amount = serializer.validated_data.get("amount")

        result = service.create_payment(
            amount,
            customer_object.patient_id,
        )

        return Response({"data": result})


class VerifyPhonePePayment(GenericAPIView):

    authentication_classes = []
    permission_classes = []
    serializer_class = []

    def post(self, request, pk):

        customer_object = self.get_object()
        gateway = PhonePeGateway()
        service = PaymentService(gateway)
        payment_object = (
            Payment.objects.filter(
                is_paid=False, is_refunded=False, patient_id=cust_object
            )
            .order_by("-created_at")
            .first()
        )
        result = service.verify_payment({"order_id": payment_object.order_id})
        return Response({"data": result})
