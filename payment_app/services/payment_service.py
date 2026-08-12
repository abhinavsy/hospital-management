from core.models import Payment



class PaymentService:

    def __init__(self,gateway):

        self.gateway = gateway

    def create_payment(
            self,
            amount,
            patient_id,
            currency : str = "INR"

    ):
        order_id =self.gateway.create_order_id(patient_id)
        # Save payment before calling Paytm
        payment = Payment.objects.create(
            order_id=order_id,
            patient_id=patient_id,
            amount=amount,
            currency=currency,
            status="PENDING",
            gateway="PAYTM",
        )

        response = self.gateway.create_payment_order(
            amount=amount,
            currency=currency,
            order_id=order_id,
            patient_id=patient_id,
        )

        return {
            "order_id": order_id,
            "payment_id": payment.id,
            "paytm_response": response,
        }

    def verify_payment(self,order_id:str):

        response = self.gateway.verify_payment(order_id)

        return response