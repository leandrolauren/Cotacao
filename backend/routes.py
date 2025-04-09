import logging
import os
import traceback

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.testclient import TestClient

from backend.auth import Auth
from backend.calculation import Calculation
from backend.database import Database
from backend.models import (
    CalculationRequest,
    HistoryRecord,
    PaginatedHistory,
    RequestHistoryParams,
    ResponseCalculation,
)

auth = Auth()
calc = Calculation()
db = Database()

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/stock/{ticker}")
def get_stock(ticker: str) -> dict:
    """_summary_
    Args:
        ticker (str): Stock ticker symbol.
    Returns:
        dict: Dictionary containing stock information.
    """

    logger.info(f"Fetching stock info for {ticker}")

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        variation = calc.calculate_variation(info)

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
    token = params.token
    if not token:
        logger.warning("Token is required for this endpoint.")
        raise HTTPException(
            status_code=401,
            detail="Token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not auth.verify_token(token):
        logger.warning("Invalid token.")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    logger.info(f"Starting calculation: {dict(request)}")

    try:
        total_value, amount_invested, total_interest, months = calc.calculate_totals(
            request.initial_value,
            request.monthly_contribution,
            request.annual_interest,
            request.months,
            request.token,
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
    logger.info("Verifying access token.")
    try:
        payload = auth.verify_token(token)

        if not payload:
            logger.warning("Invalid access token.")
            raise HTTPException(
                status_code=401,
                detail="Invalid access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info("Access token verified successfully.")
        return {"token": token, "user": payload["sub"]}
    except HTTPException as e:
        logger.error(f"HTTP Error during token verification: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="An error occurred while verifying the token."
        )


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint for user login, returning an access token.
    """
    logger.info(f"User login attempt: {form_data.username}")
    try:
        user = db.get_user_from_db(form_data.username)

        if not user or not auth.verify_password(
            form_data.password, user["password_hash"]
        ):
            logger.warning(f"Invalid login attempt for user: {form_data.username}")
            raise HTTPException(
                status_code=400,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = auth.create_access_token(data={"sub": user["email"]})
        logger.info(f"User {form_data.username} logged in successfully.")

        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        logger.error(f"HTTP Error during login: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during login: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="An error occurred during login.")


@router.post("/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint for user registration.
    """
    logger.info(f"User registration attempt: {form_data.username}")
    try:

        if not form_data.username or not form_data.password:
            logger.warning("Username and password are required.")
            raise HTTPException(
                status_code=400,
                detail="Username and password are required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.get_user_from_db(form_data.username)

        if user.get("success"):
            logger.warning(f"User {form_data.username} already exists.")
            raise HTTPException(
                status_code=400,
                detail="User already exists",
                headers={"WWW-Authenticate": "Bearer"},
            )

        db.user_register(form_data.username, form_data.password)
        logger.info(f"User {form_data.username} registered successfully.")

        return {"message": "User registered successfully."}
    except HTTPException as e:
        logger.error(f"HTTP Error during registration: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during registration: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail="An error occurred during registration."
        )


@router.get("/test")
def test_full_flow():
    if os.getenv("ENVIRONMENT") != "development":
        print("Skipping tests as the environment is not development.")
        return

    client = TestClient(router)

    # Verify the valid login
    login_response = client.post(
        "/login",
        data={
            "username": "leandro@gmail.com",
            "password": "123456789",
            "grant_type": "password",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    print(f"✅ Test Login: OK \nToken: {token}")

    # Verify the token
    token_response = client.post("/token", headers={"Authorization": f"Bearer {token}"})
    assert token_response.status_code == 200
    assert token_response.json()["user"] == "leandro@gmail.com"
    print("✅ Test valid Token: OK")

    # Verify the invalid login
    invalid_response = client.post(
        "/token",
        headers={
            "Authorization": "invalid_token",
        },
    )
    assert invalid_response.status_code == 401
    print("✅ Test invalid Token: OK")
