import logging
import traceback

from fastapi import APIRouter, Header, HTTPException

from backend.models import CalculationRequest, ResponseCalculation

logger = logging.getLogger(__name__)

calculation_router = APIRouter(tags=["Calculation"])


@calculation_router.post("/calculation", response_model=ResponseCalculation)
def calculate(
    request: CalculationRequest, authorization: str = Header(..., alias="Authorization")
) -> dict:
    """
    Perform a financial calculation based on the provided request data.
    Args:
        request (CalculationRequest): The calculation request data.
        authorization (str): The access token provided in the Authorization header.
    Returns:
        ResponseCalculation: The result of the calculation.
    """
    try:
        from backend.core.auth import Auth

        auth = Auth()
        if not auth.verify_token(access_token=authorization):
            logger.warning("Invalid token.")
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"Starting calculation: {dict(request)}")

        from backend.core.calculation import Calculation

        calc = Calculation()
        total_value, amount_invested, total_interest, months = calc.calculate_totals(
            initial_value=request.initial_value,
            monthly_contribution=request.monthly_contribution,
            annual_interest=request.annual_interest,
            number_months=request.months,
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
