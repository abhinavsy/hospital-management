import razorpay
import random

class RazorPayPayment:

    client_id = "CLIENT KEY"
    secret_key = "SECRET KEY"

    def __init__(self,amount,customer_id) :
        self.amount = amount
        self.customer_id = customer_id
    @staticmethod
    def convert_inr_to_subunits(amount):
        return amount *100

    # @staticmethod
    # def create_order_id():
    #     return random.