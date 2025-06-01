from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Model for payment item
class Item(BaseModel):
    title: str = Field(..., description="Product name")
    description: Optional[str] = Field(
        None, description="Product description (optional)"
    )
    quantity: int = Field(..., gt=0, description="Quantity")
    unit_price: float = Field(..., gt=0, description="Unit price")


# Model for payment request
class PreferenceRequest(BaseModel):
    items: list[Item] = Field(..., description="List of items")
    payer_email: EmailStr = Field(..., description="Payer's email")


# Model for payment response
class PreferenceResponse(BaseModel):
    init_point: str = Field(..., description="URL to initiate the payment")
    preference_id: str = Field(..., description="Id of preference created")


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
