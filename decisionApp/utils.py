from datetime import datetime, timedelta, timezone
from loanObjects import RepaymentEvent, RepaymentSchedule
def get_current_date()->datetime:
    return datetime.now(timezone(timedelta(hours=1))) 

def get_start_date(days : int)->datetime:
    return get_current_date() + timedelta(days=days)

def generate_repayment_schedule(
    duration_months: int, monthly_payment: float, start_offset_days: int = 10
) -> RepaymentSchedule:
    """
    Generate a repayment schedule with equal monthly payments.

    :param duration_months: Total number of months for repayment.
    :param monthly_payment: Fixed monthly payment amount.
    :param start_offset_days: Days after approval when the first payment starts.
    :return: RepaymentSchedule object.
    """
    start_date = get_start_date(start_offset_days)  # Returns a datetime object

    repayment_events = [
        RepaymentEvent(
            payment_date=(start_date + timedelta(days=30 * i)).strftime("%Y-%m-%d"),  # Convert to string
            amount=monthly_payment
        )
        for i in range(duration_months)
    ]

    return RepaymentSchedule(
        start_date=start_date.strftime("%Y-%m-%d"),  # Convert to string
        repaymentEvent=repayment_events
    )
