import yookassa
from yookassa import Payment
import uuid

yookassa.Configuration.account_id = "000000"
yookassa.Configuration.secret_key = "..."

def create(payment, chat_id):
	id_key = uuid.uuid4()
	payment = Payment.create({
	    "amount": {
	        "value": f"{payment:0.2f}",
	        "currency": "RUB"
	    },
	    "receipt": {
            "customer": {
                "full_name": "Ivanov Ivan Ivanovich",
                "email": "email@email.ru",
                "phone": "79211234567",
                "inn": "6321341814"
            },
            "items": [
                {
                    "description": "Предложение",
                    "quantity": "1.00",
                    "amount": {
                        "value": payment,
                        "currency": "RUB"
                    },
                    "vat_code": "2",
                    "payment_mode": "full_payment",
                    "payment_subject": "commodity",
                    "country_of_origin_code": "CN",
                    "product_code": "44 4D 01 00 21 FA 41 00 23 05 41 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 12 00 AB 00",
                    "customs_declaration_number": "10714040/140917/0090376",
                    "excise": "20.00",
                    "supplier": {
                        "name": "string",
                        "phone": "string",
                        "inn": "string"
                    }
                },
            ]
	    },
	    "payment_method_data": {
	        "type": "bank_card"
	    },
	    "confirmation": {
	        'type': 'redirect',
	        'return_url': 'https://t.me/Testx100000Bot'
	    },
	    'capture': True,
	    'metadata': {
	        'chat_id': chat_id
	    },
	    "description": "Предложение",
	    	
	}, id_key)
	return payment.confirmation.confirmation_url, payment.id
	
def check(payment_id):
	payment = Payment.find_one(payment_id)
	if payment.status == "succeeded":
		return payment.metadata
	else:
		return False