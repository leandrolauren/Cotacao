import logging
import traceback

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request

from backend.core.rate_limit import limiter
from backend.core.stock import Stock
from backend.models import PaginatedHistory, RequestHistoryParams

logger = logging.getLogger(__name__)

stock_router = APIRouter(tags=["Stock"])


@stock_router.get("/stock/{ticker}")
@limiter.limit("10/minute")
def get_stock(
    request: Request,
    ticker: str = Path(
        ...,
        min_length=1,
        max_length=6,
        pattern="^[A-Z0-9.]+$",
        description="Stock ticker symbol (e.g., AAPL, MSFT)",
    ),
    authorization: str = Header(..., alias="Authorization"),
) -> dict:
    """_summary_
    Args:
        ticker (str): Stock ticker symbol.
    Returns:
        dict: Dictionary containing stock information.

    """
    from backend.core.auth import Auth

    auth = Auth()
    if not auth.verify_token(access_token=authorization):
        logger.warning("Invalid token.")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        if not ticker.isalnum() and ticker != ".":
            raise HTTPException(status_code=400, detail="Invalid ticker format.")

        logger.info(f"Fetching stock info for {ticker}")
        stock = Stock(symbol=ticker)

        info = stock.fetch_data()

        if info:
            from backend.core.calculation import Calculation

            calc = Calculation()
            variation = calc.calculate_variation(info["data"])
            info["data"]["Variation"] = variation

        if not info or not info.get("success", False):
            raise HTTPException(
                status_code=404, detail="Stock ticker not found or invalid."
            )

        logger.info(f"Fetched stock info for {ticker}")

        return info

    except Exception as e:
        if "rate limit" in str(e).lower():
            logger.warning(f"Rate limit exceeded.")
            logger.error(f"Error fetching stock info for {ticker}: {str(e)}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
            )

        logger.error(f"Error fetching stock info for {ticker}: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching stock info."
        )


@stock_router.get("/history", response_model=PaginatedHistory)
@limiter.limit("50/minute")
def get_history(
    request: Request,
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
    from backend.core.auth import Auth

    auth = Auth()

    if not auth.verify_token(access_token=authorization):
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
        stock = Stock(symbol=params.ticker)
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
