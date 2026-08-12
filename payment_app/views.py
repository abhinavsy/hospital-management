# Create your views here.
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.generics import GenericAPIView

from payment_app.services.payment_service import PaymentService
from payment_app.services.paytm_pg_service import PaytmGateway
from core.models import Patient, Payment
from rest_framework.response import Response
from rest_framework import status


class CreatePaytmPaymentView(GenericAPIView):

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


class VerifyPayment(GenericAPIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request, pk):

        cust_object = self.get_object()
        gateway = PaytmGateway()
        payment_object = (
            Payment.objects.filter(is_paid=False, is_refunded=False, patient_id=Patient)
            .order_by("-created_at")
            .first()
        )

        response = gateway.verify_payment({"order_id": payment_object.order_id})
        return Response(
            {
                "data": response,
            },
            status.HTTP_200_OK,
        )
