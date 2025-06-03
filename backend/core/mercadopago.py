import logging
import os
from typing import Dict, List

import mercadopago as mp

from backend import db_connection
from backend.core.stock import Stock

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """Class to handle payment processing using MercadoPago SDK."""

    def __init__(self):
        self.access_token = os.getenv("MP_TEST_TOKEN")
        if not self.access_token:
            raise ValueError("Access token not configured.")
        self.sdk = mp.SDK(self.access_token)

    def create_payment_preference(self, user_id: int, items: List[dict]) -> dict:
        """
        Creates a payment preference and registers pending transaction(s).

        Args:
            user_id: ID of the user making the purchase
            items: List of items (stock_symbol, quantity)

        Returns:
            Dict containing payment_url and transaction_ids
        """
        # Get user email
        email_payer = db_connection.get_email_user_by_id(user_id)
        if not email_payer:
            logger.error(f"User with ID {user_id} not found.")
            raise ValueError(f"User with ID {user_id} not found.")

        mp_items = []
        transaction_ids = []

        try:
            for item in items:
                stock = Stock(item["symbol"])
                stock_data = stock.fetch_data()
                if not stock_data["success"]:
                    logger.error(f"Could not fetch data for stock {item['symbol']}")
                    raise ValueError(f"Failed to fetch price for: {item['symbol']}")

                current_price = stock_data["data"]["Actual Price"]
                total_amount = current_price * item["quantity"]

                # Insert transaction record
                insert_query = """
                    INSERT INTO transactions 
                        (user_id, stock_symbol, quantity, price,type, status)
                    VALUES
                        (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """

                result = db_connection.execute(
                    query=insert_query,
                    params=(
                        user_id,
                        item["symbol"],
                        item["quantity"],
                        current_price,
                        "buy",
                        "pending",
                    ),
                )
                transaction_id = result[0] if isinstance(result, tuple) else result
                transaction_ids.append(transaction_id)

                mp_items.append(
                    {
                        "title": f"{item['quantity']} x {item['symbol']} shares",
                        "quantity": 1,
                        "unit_price": float(total_amount),
                        "currency_id": "BRL",
                    }
                )

            preference_data = {
                "items": mp_items,
                "payer": {"email": email_payer},
                "external_reference": ",".join(map(str, transaction_ids)),
                "notification_url": os.getenv("MP_NOTIFICATION_URL"),
                "statement_descriptor": "Leandro Stock Quote",
                "back_urls": {
                    "success": os.getenv("URL_SUCCESS"),
                    "failure": os.getenv("URL_FAILURE"),
                },
                "auto_return": "approved",
            }

            # Create payment preference
            response = self.sdk.preference().create(preference_data)
            db_connection.commit()

            return {
                "payment_url": response["response"]["sandbox_init_point"],
                "preference_id": response["response"]["id"],
                "transaction_ids": transaction_ids,
            }

        except Exception as e:
            db_connection.rollback()
            logger.error(f"Error creating payment preference: {e}")
            raise ValueError(f"Failed to create payment preference: {str(e)}") from e

    def process_webhook(self, payload: dict) -> bool:
        """
        Process webhook notification from Mercado Pago.
        Updates transaction status and user's wallet for approved payments.
        """
        try:
            payment_id = payload["data"]["id"]
            payment_status = payload["data"]["status"]
            transaction_ids = payload["external_reference"].split(",")

            for transaction_id in transaction_ids:
                self._update_transaction(transaction_id, payment_id, payment_status)

                if payment_status == "approved":
                    self._update_user_wallet(transaction_id)

            db_connection.commit()
            return True

        except Exception as e:
            db_connection.rollback()
            logger.error(f"Error processing webhook: {e}")
            raise

    def _update_transaction(self, transaction_id: int, payment_id: str, status: str):
        sql = """
        UPDATE transactions 
        SET status = %s, mp_payment_id = %s 
        WHERE id = %s
        """
        db_connection.execute(sql, (status, payment_id, transaction_id))

    def _update_user_wallet(self, transaction_id: int):
        sql = """
        SELECT user_id, stock_symbol, quantity, price 
        FROM transactions 
        WHERE id = %s
        """
        result = db_connection.execute(sql, (transaction_id,))
        if not result:
            raise ValueError(f"Transaction {transaction_id} not found")

        user_id, symbol, quantity, price = result[0]
        total_amount = price * quantity

        # Update wallet (UPSERT)
        sql_wallet = """
        INSERT INTO wallet (user_id, stock_symbol, quantity)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, stock_symbol) 
        DO UPDATE SET quantity = wallet.quantity + EXCLUDED.quantity
        """
        db_connection.execute(sql_wallet, (user_id, symbol, quantity))

        # Update user balance
        sql_balance = """
        UPDATE users 
        SET balance = balance - %s 
        WHERE id = %s
        """
        db_connection.execute(sql_balance, (total_amount, user_id))
