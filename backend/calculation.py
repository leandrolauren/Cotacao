import logging

# from backend.models import CalculationRequest

logger = logging.getLogger(__name__)


class Calculation:
    """
    Calculation class to handle financial calculations.
    """

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._instanced = True

    def calculate_monthly_rate(self, annual_rate: float) -> float:
        """
        Calculate the monthly interest rate from the annual rate.
        :param annual_rate: Annual interest rate as a percentage.
        :return: Monthly interest rate as a decimal.
        """
        if annual_rate <= 0:
            raise ValueError("Annual interest rate must be greater than zero")
        return (annual_rate / 100) / 12

    def calculate_total_value(
        self,
        initial_value: float,
        monthly_contribution: float,
        months: int,
        annual_interest: float,
    ) -> float:
        """
        Calculate the total value after a certain number of months with monthly contributions and interest.
        :param initial_value: Initial investment amount.
        :param monthly_contribution: Monthly contribution amount.
        :param months: Number of months to calculate.
        :param annual_interest: Annual interest rate as a percentage.
        :return: Total value after the specified number of months.
        """
        monthly_rate = self.calculate_monthly_rate(annual_interest)
        total_value = initial_value

        for _ in range(months):
            total_value += monthly_contribution
            fees = total_value * monthly_rate
            total_value += fees

        return total_value

    def calculate_total_invested(
        self, initial_value: float, monthly_contribution: float, months: int
    ) -> float:
        """
        Calculate the total amount invested after a certain number of months.
        :param initial_value: Initial investment amount.
        :param monthly_contribution: Monthly contribution amount.
        :param months: Number of months to calculate.
        :return: Total amount invested after the specified number of months.
        """
        return initial_value + (monthly_contribution * months)

    def calculate_total_interest(
        self,
        initial_value: float,
        monthly_contribution: float,
        months: int,
        annual_interest: float,
    ) -> dict:
        """
        Calculate the total interest earned after a certain number of months.
        :param initial_value: Initial investment amount.
        :param monthly_contribution: Monthly contribution amount.
        :param months: Number of months to calculate.
        :param annual_interest: Annual interest rate as a percentage.
        :return: Total interest earned after the specified number of months.
        """
        monthly_rate = self.calculate_monthly_rate(annual_interest)
        total_value = initial_value
        total_interest = 0
        months_results = []

        for _ in range(months):
            total_value += monthly_contribution
            fees = total_value * monthly_rate
            total_value += fees
            total_interest += fees

            months_results.append(
                {
                    "Month": _ + 1,
                    "Interest Amount": fees,
                    "Amount Invested": initial_value + (monthly_contribution * (_ + 1)),
                    "Accumulated Interest": total_interest,
                    "Accumulated Total": total_value,
                }
            )

        return total_interest, total_value, months_results


if __name__ == "__main__":
    calc = Calculation()
    initial_value = 1000
    monthly_contribution = 100
    months = 12
    annual_interest = 5
    total_value = calc.calculate_total_value(
        initial_value, monthly_contribution, months, annual_interest
    )
    total_invested = calc.calculate_total_invested(
        initial_value, monthly_contribution, months
    )
    total_interest, total_value, months = calc.calculate_total_interest(
        initial_value, monthly_contribution, months, annual_interest
    )
    print(f"Total Value: {total_value}")
    print(f"Total Invested: {total_invested}")
    print(f"Total Interest: {total_interest}")
    print("Monthly Results:")
    for month in months:
        print(month)


def calculate_variation(info: dict):
    price_before = info.get("previousClose")
    actual_price = info.get("regularMarketPrice")

    if price_before and actual_price:
        variation = ((actual_price - price_before) / price_before) * 100
        return variation
    return None


# def calculate_interest(request: CalculationRequest):
#     try:
#         logger.debug(f"Calculating with params: {request.dict()}")

#         if request.annual_interest <= 0:
#             raise ValueError("Interest rate must be greater than zero")

#         monthly_rate = (request.annual_interest / 100) / 12

#         total_value = request.initial_value
#         amount_invested = request.initial_value
#         total_interest = 0
#         months = []

#         for i in range(1, request.months + 1):

#             if i > 1:
#                 total_value += request.monthly_contribution
#                 amount_invested += request.monthly_contribution

#             fees = total_value * monthly_rate
#             total_value += fees
#             total_interest += fees

#             months.append(
#                 {
#                     "Month": i,
#                     "Interest Amount": fees,
#                     "Amount Invested": amount_invested,
#                     "Accumulated Interest": total_interest,
#                     "Accumulated Total": total_value,
#                 }
#             )

#         return total_value, amount_invested, total_interest, months

#     except Exception as e:
#         logger.error(f"Error in calculate_interest: {str(e)}")
#         raise
