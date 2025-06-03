import logging
import os
import traceback

from fastapi import APIRouter, Header, HTTPException, Request

from backend.core.auth import Auth
from backend.core.mercadopago import PaymentProcessor
from backend.core.rate_limit import limiter
from backend.payment_model import (
    MPCallback,
    MPCallbackResponse,
    PaymentRequest,
    PaymentResponse,
)

logger = logging.getLogger(__name__)
payment_router = APIRouter(tags=["Payments"])


@payment_router.post("/payments/create", response_model=PaymentResponse)
@limiter.limit("5/minute")
async def create_payment(
    request: Request,
    payment_request: PaymentRequest,
    authorization: str = Header(..., alias="Authorization"),
):
    """
    Create a payment preference using MercadoPago.

    Args:
        preference (PreferenceRequest): Payment preference data.
        authorization (str): Authorization token.

    Returns:
        PreferenceResponse: Response containing the payment URL and status.
    """

    auth = Auth()
    if not auth.verify_token(access_token=authorization):
        logger.warning("Invalid token.")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        processor = PaymentProcessor()
        items = [
            {"symbol": item.symbol, "quantity": item.quantity}
            for item in payment_request.items
        ]

        if not items:
            logger.error("Items list cannot be empty.")
            raise HTTPException(status_code=400, detail="Items list cannot be empty")

        result = processor.create_payment_preference(
            user_id=payment_request.user_id, items=items
        )

        return PaymentResponse(
            payment_url=result["payment_url"],
            transaction_ids=result["transaction_ids"],
        )

    except ValueError as ve:
        logger.error(f"Error creating payment preference: {ve}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.error(f"Error creating payment preference: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")


mp_callback_router = APIRouter(tags=["MercadoPago Callback"])


@mp_callback_router.get("/payment/success", response_model=MPCallbackResponse)
async def payment_success(request: Request) -> MPCallbackResponse:
    """
    Receive parameter from MercadoPago when payment is successful.
    """
    params = request.query_params

    logger.info("MercadoPago callback received")

    callback_data = {key: value for key, value in params.items()}

    try:
        validate_callback = MPCallback(**callback_data)

    except Exception as e:
        logger.error(f"Invalid callback data: {e}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=400, detail="Invalid callback data format")

    logger.info("Callback data validated successfully")

    return MPCallbackResponse(success=True, data=validate_callback)


@payment_router.post("/payments/webhook")
async def payment_webhook(
    request: Request,
    x_signature: str = Header(...),
):
    """Handle Mercado Pago webhook notifications."""
    if x_signature != os.getenv("MP_WEBHOOK_SECRET"):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = await request.json()
        processor = PaymentProcessor()
        processor.process_webhook(payload)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
