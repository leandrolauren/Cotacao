from pydantic import BaseModel, Field
from typing import List, Optional


# Output model for a single historical record
class HistoryRecord(BaseModel):
    date: str = Field(..., title="Date", description="Date of the record")
    close: float = Field(..., description="Price of the closing of the stock")
    message: Optional[str] = Field(None, description="Message for the user")


# Model for output with history pagination
class PaginatedHistory(BaseModel):
    success: bool = Field(..., description="Indicates whether the query was successful")
    data: List[HistoryRecord] = Field(..., description="List of historical records")
    pagination: dict = Field(
        ..., description="Info for pagination (actual page, total pages, etc.)"
    )
    message: Optional[str] = Field(None, description="Message for the user")


# Model for input validation
class RequestHistoryParams(BaseModel):
    ticker: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Symbol of the stock, e.g., 'AAPL'",
    )
    days: int = Field(
        ...,
        gt=0,
        le=365,
        description="Number of days for consulting the history of the stock (between 1 and 365)",
    )

    page: int = Field(
        gt=0, description="Number of the page for pagination (default: 1)"
    )


# Model for Calculate validation
class CalculationRequest(BaseModel):
    initial_value: float = Field(
        ..., ge=0.0, description="Initial value for calculate", title="Initial Value"
    )
    monthly_contribution: float = Field(
        ...,
        ge=0.0,
        description="Monthly contribution amount",
        title="Monthly Contribution",
    )
    annual_interest: float = Field(
        ..., gt=0.0, description="Annual interest rate.", title="Annual Interest"
    )
    months: int = Field(
        ..., gt=0, description="Number of months for calculation", title="Months"
    )


# Model for response calculated
class ResponseCalculation(BaseModel):
    success: bool = Field(..., description="Indicates whether the query was successful")
    data: dict = Field(..., description="Dictionary of values for each month.")
    message: Optional[str] = Field(None, description="Message for the user.")
