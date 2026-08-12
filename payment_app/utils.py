import uuid
from abc import ABC, abstractmethod
from decimal import ROUND_HALF_UP, Decimal


class PaymentGateway(ABC):

    @abstractmethod
    def create_payment_order(self, amount, currency, order_id, payment_id):
        raise NotImplementedError

    @abstractmethod
    def verify_payment(self, payment_data: dict):
        raise NotImplementedError

    @staticmethod
    def create_order_id(patient_id):
        """To create orderid for razorpay transactions"""
        return f"patient_{patient_id}_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def convert_inr_to_subunits(amount):
        """To convert Rupees to in range or paisa"""
        return int(
            (amount * 100).quantize(
                Decimal(1),
                rounding=ROUND_HALF_UP,
            )
        )
