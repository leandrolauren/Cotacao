import logging
import traceback

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from backend.auth import Auth
from backend.calculation import calculate_interest, calculate_variation
from backend.database import get_user_from_db
from backend.models import (
    CalculationRequest,
    HistoryRecord,
    PaginatedHistory,
    RequestHistoryParams,
    ResponseCalculation,
)

auth = Auth()

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stock/{ticker}")
def get_stock(ticker: str) -> dict:

    logger.info(f"Fetching stock info for {ticker}")

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        variation = calculate_variation(info)

        if not info:
            raise HTTPException(
                status_code=404, detail="Stock ticker not found or invalid."
            )

        logger.info(f"Fetched stock info for {ticker}")

        return {
            "success": True,
            "data": {
                "Name": info.get("shortName"),
                "P/E": info.get("trailingPE"),
                "EBITDA": info.get("ebitda"),
                "Gross Margin": float(info.get("grossMargins") * 100),
                "Net Margin": float(info.get("profitMargins") * 100),
                "Sector": info.get("sector"),
                "Industry": info.get("industry"),
                "Description": info.get("longBusinessSummary"),
                "Actual Price": info.get("currentPrice"),
                "Variation": variation,
            },
            "message": "Stock info fetched successfully",
        }
    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error ocurred while fetching stock info."
        )


@router.get("/history", response_model=PaginatedHistory)
def get_history(params: RequestHistoryParams = Depends()):

    logger.info(
        f"Fetching closing prices for {params.ticker} over the last {params.days} days (page {params.page})"
    )

    try:
        #
        stock = yf.Ticker(params.ticker)
        history = stock.history(period=f"{params.days}d")

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail="No historical data found for the specified ticker and time period.",
            )

        # Pagination
        history.reset_index(inplace=True)
        history = history[["Date", "Close"]]
        page_size = 100
        start = (params.page - 1) * page_size
        end = start + page_size

        paginated_history = history.iloc[start:end]
        if paginated_history.empty:
            raise HTTPException(
                status_code=404, detail="No data available for the requested page."
            )

        records = [
            HistoryRecord(date=row["Date"].strftime("%Y-%m-%d"), close=row["Close"])
            for _, row in paginated_history.iterrows()
        ]

        logger.info(f"Fetched closing prices for {params.ticker} (page {params.page})")

        return PaginatedHistory(
            success=True,
            pagination={
                "current_page": params.page,
                "page_size": page_size,
                "total_pages": (len(history) + page_size - 1) // page_size,
                "total_records": len(history),
            },
            data=records,
            message="Historical data fetched successfully.",
        )

    except HTTPException as e:
        logger.error(f"HTTP Error: {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"Error fetching historical data for {params.ticker}: {e}")
        raise HTTPException(
            status_code=500, detail="An error ocurred while fetcing historical data."
        )


@router.post("/calculation", response_model=ResponseCalculation)
def calculate(request: CalculationRequest) -> dict:
    logger.info(f"Starting calculation: {request.dict()}")

    try:
        total_value, amount_invested, total_interest, months = calculate_interest(
            request
        )

        logger.info("Calculation ended successfully.")

        return ResponseCalculation(
            success=True,
            data={
                "total_value": total_value,
                "amount_invested": amount_invested,
                "total_interest": total_interest,
                "months": months,
            },
            message="Calculation Performed.",
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))

    except HTTPException as e:
        logger.error(f"HTTP Error: {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"Unexpected error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/token")
def get_token(token: str = Depends(auth.oauth2_scheme)):
    """
    Endpoint to verify the access token.
    """
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"token": token, "user": payload["sub"]}


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint for user login, returning an access token.
    """
    logger.info(f"User login attempt: {form_data.username}")
    user = get_user_from_db(form_data.username)

    if not user or not auth.verify_password(form_data.password, user["password_hash"]):
        logger.warning(f"Invalid login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}
