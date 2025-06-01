import os

import mercadopago as mp


class PaymentProcessor:
    """Class to handle payment processing using MercadoPago SDK."""

    def __init__(self):
        self.access_token = os.getenv("MP_TEST_TOKEN")
        if not self.access_token:
            raise ValueError("Access token not configured.")
        self.sdk = mp.SDK(self.access_token)

    def create_preference(self, items: list, email_payer: str) -> dict:
        """
        Create a payment preference using the MercadoPago SDK.

        Args:
            items (list): List of items to be paid. Each item must be a dictionary with the keys:
                - title: (str) product name
                - description: (str) product description (optional)
                - quantity: (int) quantity of the product
                - unit_price: (float) unity price of the product
            payer (str): Payer information, example:
                - email: (str)

        Returns:
            dict: MercadoPago API response containing information about the created preference.
        """

        preference_data = {
            "items": items,
            "payer": email_payer,
            "back_urls": {
                "success": os.getenv("URL_SUCCESS"),
                "failure": os.getenv("URL_FAILURE"),
            },
            "auto_return": "approved",
        }
        preference_response = self.sdk.preference().create(preference_data)
        return preference_response["response"]
