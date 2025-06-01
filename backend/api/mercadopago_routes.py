import logging
import traceback

from fastapi import APIRouter, Header, HTTPException, Request

from backend.core.rate_limit import limiter
from backend.payment_model import (
    MPCallback,
    MPCallbackResponse,
    PreferenceRequest,
    PreferenceResponse,
)

logger = logging.getLogger(__name__)
payment_router = APIRouter(tags=["Payments"])


@payment_router.post("/payment/checkout", response_model=PreferenceResponse)
@limiter.limit("5/minute")
async def create_payment_preference(
    request: Request,
    preference: PreferenceRequest,
    authorization: str = Header(..., alias="Authorization"),
) -> PreferenceResponse:
    """
    Create a payment preference using MercadoPago.

    Args:
        preference (PreferenceRequest): Payment preference data.
        authorization (str): Authorization token.

    Returns:
        PreferenceResponse: Response containing the payment URL and status.
    """
    from backend.core.auth import Auth
    from backend.core.mercadopago import PaymentProcessor

    auth = Auth()
    if not auth.verify_token(access_token=authorization):
        logger.warning("Invalid token.")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        logger.info("Creating payment preference.")

        items = [
            {
                "title": item.title,
                "description": item.description or "",
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in preference.items
        ]
        if not items:
            logger.error("Items list cannot be empty.")
            raise HTTPException(status_code=400, detail="Items list cannot be empty")
        payer_email = preference.payer_email.strip().lower()

        if not payer_email:
            logger.error("Payer email is required.")
            raise HTTPException(status_code=400, detail="Payer email is required")

        processor = PaymentProcessor()
        response = processor.create_preference(items, payer_email)

        if not response or "sandbox_init_point" not in response:
            logger.error("Failed to create payment preference.")
            raise HTTPException(
                status_code=500, detail="Failed to create payment preference"
            )
        logger.info("Payment preference created successfully.")

        return PreferenceResponse(
            init_point=response["sandbox_init_point"], preference_id=response["id"]
        )
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
