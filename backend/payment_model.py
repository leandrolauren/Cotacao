from typing import List, Optional

from pydantic import BaseModel, Field


# Model for payment item
class PaymentItem(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g., 'AAPL')")
    quantity: int = Field(..., gt=0, description="Quantity")


# Model for payment request
class PaymentRequest(BaseModel):
    user_id: int = Field(..., gt=0, description="User ID")
    items: list[PaymentItem] = Field(..., description="List of items")


# Model for payment response
class PreferenceResponse(BaseModel):
    init_point: str = Field(..., description="URL to initiate the payment")
    preference_id: str = Field(..., description="Mercado Pago preference ID")


class PaymentResponse(BaseModel):
    payment_url: str = Field(..., description="Mercado Pago checkout URL")
    transaction_ids: List[int] = Field(..., description="IDs of created transactions")


class WebhookPayload(BaseModel):
    id: str
    type: str
    data: dict


class MPCallback(BaseModel):
    collection_id: str = Field(..., description="Collection ID")
    collection_status: str = Field(..., description="Collection status")
    payment_id: str = Field(..., description="Payment ID")
    status: str = Field(..., description="Payment status")
    external_reference: Optional[str] = Field(None, description="External reference")
    payment_type: str = Field(..., description="Payment type")
    merchant_order_id: str = Field(..., description="Merchant order ID")
    preference_id: str = Field(..., description="Preference ID")
    site_id: str = Field(..., description="Site ID")
    processing_mode: str = Field(..., description="Processing mode")
    merchant_account_id: Optional[str] = Field(
        None, description="Merchant account ID (optional)"
    )


class MPCallbackResponse(BaseModel):
    success: bool = Field(
        ..., description="Indicates whether the callback was successful"
    )
    data: MPCallback = Field(..., description="Data from the MercadoPago callback")
