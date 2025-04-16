import logging

from backend.core.auth import Auth

auth = Auth()

logger = logging.getLogger(__name__)


class Calculation:
    """
    Calculation class to handle financial calculations.
    """

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern to ensure only one instance of Calculation exists.
        """
        if not hasattr(cls, "_instance"):
            cls._instance = super(Calculation, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True

    def calculate_monthly_rate(self, annual_rate: float) -> float:
        """_summary_
        Args:
            :param annual_rate: Annual interest rate as a percentage.
            :return: Monthly interest rate as a decimal.
        """
        if annual_rate <= 0:
            raise ValueError("Annual interest rate must be greater than zero")
        return (annual_rate / 100) / 12

    def calculate_totals(
        self,
        initial_value: float,
        monthly_contribution: float,
        annual_interest: float,
        number_months: int,
    ) -> float:
        """_summary_

        Args:
            param: initial_value (float): Initial value for the calculation.
            param: monthly_contribution (float): Monthly contribution amount.
            param: annual_interest (float): Annual interest rate as a percentage.
            param: months (int): Number of months for the calculation.

        Raises:
            ValueError: If the annual interest rate is less than or equal to zero.

        Returns:
            float: The total value after the specified number of months.
        """
        try:

            if annual_interest <= 0:
                raise ValueError("Interest rate must be greater than zero")

            monthly_rate = self.calculate_monthly_rate(annual_interest)

            total_value = initial_value
            amount_invested = initial_value
            total_interest = 0
            months = []

            for i in range(1, number_months + 1):

                if i > 1:
                    total_value += monthly_contribution
                    amount_invested += monthly_contribution

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

        except PermissionError as e:
            logger.error(f"Authentication error: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Error in calculate_interest: {str(e)}")
            raise

    def calculate_variation(self, info: dict):
        """_summary_
        Args:
            info (dict): Dictionary containing stock information.
                Expected keys: 'previousClose' and 'regularMarketPrice'.
        Returns:
            float: Percentage variation between previous close and current market price.
        """
        if not isinstance(info, dict):
            raise ValueError("info must be a dictionary")

        try:
            price_before = info.get("Previous Close")
            actual_price = info.get("Regular Market Price")
            short_name = info.get("Name", "Unknown")
            logger.info(
                f"Calculating variation for {short_name}. Previous Close: {price_before}, Regular Market Price: {actual_price}"
            )

            if price_before and actual_price:
                variation = ((actual_price - price_before) / price_before) * 100
                logger.info(f"Variation calculated: {variation:.2f}%")
                return variation
        except KeyError as e:
            logger.error(f"Key error: {str(e)}")
            raise ValueError(f"Missing key in info dictionary: {str(e)}")

        except Exception as e:
            logger.error(f"Error calculating variation: {str(e)}")
            raise ValueError(f"Error calculating variation: {str(e)}")

        return None
