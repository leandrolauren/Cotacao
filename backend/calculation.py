from models import CalculationRequest
import logging

logger = logging.getLogger(__name__)


def calculate_variation(info: dict):
    price_before = info.get("previousClose")
    actual_price = info.get("regularMarketPrice")

    if price_before and actual_price:
        variation = ((actual_price - price_before) / price_before) * 100
        return variation
    return None


def calculate_interest(request: CalculationRequest):
    try:
        logger.debug(f"Calculating with params: {request.dict()}")

        if request.annual_interest <= 0:
            raise ValueError("Interest rate must be greater than zero")

        monthly_rate = (request.annual_interest / 100) / 12

        total_value = request.initial_value
        amount_invested = request.initial_value
        total_interest = 0
        months = []

        for i in range(1, request.months + 1):

            if i > 1:
                total_value += request.monthly_contribution
                amount_invested += request.monthly_contribution

            fees = total_value * monthly_rate
            total_value += fees
            total_interest += fees

            months.append(
                {
                    "Month": i,
                    "Interest Amount": fees,
                    "Amount Invested": amount_invested,
                    "Accumulated Interest": total_interest,
                    "Accumulated Total": total_value,
                }
            )

        return total_value, amount_invested, total_interest, months

    except Exception as e:
        logger.error(f"Error in calculate_interest: {str(e)}")
        raise
