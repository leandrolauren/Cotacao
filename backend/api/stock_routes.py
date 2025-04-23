import logging
import traceback

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.core.auth import Auth
from backend.core.calculation import Calculation
from backend.core.database import Database
from backend.core.stock import Stock
from backend.models import PaginatedHistory, RequestHistoryParams

auth = Auth()
calc = Calculation()
db = Database()

logger = logging.getLogger(__name__)

stock_router = APIRouter(tags=["Stock"])


@stock_router.get("/stock/{ticker}")
def get_stock(
    ticker: str, authorization: str = Header(..., alias="Authorization")
) -> dict:
    """_summary_
    Args:
        ticker (str): Stock ticker symbol.
    Returns:
        dict: Dictionary containing stock information.

    """
    if not auth.verify_token(access_token=authorization, db_instance=db):
        logger.warning("Invalid token.")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        logger.info(f"Fetching stock info for {ticker}")
        stock = Stock(ticker)

        info = stock.fetch_data()

        if info:
            variation = calc.calculate_variation(info["data"])
            info["data"]["Variation"] = variation

        if not info or not info.get("success", False):
            raise HTTPException(
                status_code=404, detail="Stock ticker not found or invalid."
            )

        logger.info(f"Fetched stock info for {ticker}")

        return info

    except Exception as e:
        logger.error(f"Error fetching stock info for {ticker}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching stock info."
        )


@stock_router.get("/history", response_model=PaginatedHistory)
def get_history(
    params: RequestHistoryParams = Depends(),
    authorization: str = Header(..., alias="Authorization"),
) -> PaginatedHistory:
    """
    Fetch historical stock data for a given ticker symbol.
    Args:
        params (RequestHistoryParams): Parameters for fetching historical data.
        token (str): Authentication token.
    Returns:
        PaginatedHistory: Paginated historical stock data.
    """

    if not auth.verify_token(access_token=authorization, db_instance=db):
        logger.warning("Invalid token.")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        logger.info(
            f"Fetching historical data for {params.ticker} over the last {params.days} days (page {params.page})"
        )
        stock = Stock(params.ticker)
        return stock.fetch_historical_data(params.days, params.page)

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))

    except HTTPException as e:
        logger.error(f"HTTP Error: {e.detail}")
        raise e

    except Exception as e:
        logger.error(
            f"Error fetching historical data for {params.ticker}: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching historical data."
        )
