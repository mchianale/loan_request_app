from datetime import datetime, timedelta, timezone
# https://www.empruntis.com/financement/actualites/barometres_regionaux.php
PENALITIES = {
    "Paid on time": 0.1,
    "Paid late": 0.3,
    "Never paid": 0.9,
    "Ongoing": 0.1,
    "Completed": 0.5,
    "Canceled": 1.0
}


def get_current_date()->datetime:
    return datetime.now(timezone(timedelta(hours=1))) 

def get_age(date_of_birth: str) -> int:
    """
    Calculates the age from a given birth date.

    Parameters:
    date_of_birth (str): Birth date in "YYYY-MM-DD" format.

    Returns:
    int: Age in years.
    """
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
        today = get_current_date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

def get_monthly_rate(annual_rate: float) -> float:
    """
    Converts an annual interest rate to a monthly interest rate.

    Parameters:
    annual_rate (float): The annual interest rate (percentage).

    Returns:
    float: The monthly interest rate (decimal, not percentage).
    """
    return (annual_rate / 100) / 12

def get_monthly_payment(loan_amount: float, duration_months: float, monthly_rate : float) -> float:
    """
    Calculates the monthly payment for a fixed-rate loan.

    Parameters:
    loan_amount (float): The total loan amount.
    monthly_rate (float): The monthly interest rate (decimal, not percentage).
    duration_months (float): The loan duration in months.

    Returns:
    float: The monthly payment amount.
    """
    if monthly_rate == 0:  # If interest rate is 0, it's a simple division
        return loan_amount / duration_months

    return round((loan_amount * monthly_rate) / (1 - (1 + monthly_rate) ** -duration_months), 2)

def evaluate_user_credits(user_credits: list, date_of_birth: str) -> dict:
    all_monthly_payment = 0
    counter = {
        "Ongoing": 0,
        "Completed": 0,
        "Canceled": 0,
        # payment
        "Paid on time": 0,
        "Paid late": 0,
        "Never paid": 0
    }
    for credit in user_credits:
        counter[credit.status.value] += 1
        for payment in credit.payment_history:
            counter[payment.status.value] += 1
        if credit.status.value == "Ongoing":
            monthly_rate = get_monthly_rate(credit.annual_rate)
            all_monthly_payment += get_monthly_payment(credit.amount, credit.duration_months, monthly_rate)

    total = sum(counter.values())
    if total > 0:
        pos_score = (counter["Paid on time"] * PENALITIES["Paid on time"] + counter["Completed"] * PENALITIES["Completed"]) / total
        neg_score = 1 - (counter["Never paid"] * PENALITIES["Never paid"] + counter["Canceled"] * PENALITIES["Canceled"] + counter["Ongoing"] * PENALITIES["Ongoing"]) / total
    else:
        age = min(get_age(date_of_birth), 130)
        pos_score = 0
        neg_score = 0.8*(130-age)/130  # having no history at an older age raises more concerns than at a younger age.
    credit_score = (pos_score + neg_score)/2 # mean of positive and negative scores
    credit_score *= 100
    return {
        "credit_score": credit_score,
        "all_monthly_payment": all_monthly_payment
    }

def get_dti(gross_monthly_income: float, monthly_payment: float) -> float:
    """
    Calculates the debt-to-income ratio.

    Parameters:
    gross_monthly_income (float): The gross monthly income.
    monthly_payment (float): The monthly payment amount.

    Returns:
    float: The debt-to-income ratio.
    """
    dti =  (monthly_payment / gross_monthly_income)*100 if gross_monthly_income != 0 else 10
    return min(100.0, dti)

def get_work_score(work_status: str) -> float:
    """
    Returns a score based on the user's work status.

    Parameters:
    work_status (str): The user's work status.

    Returns:
    float: The work status score.
    """
    if work_status == "Employed":
        return 100
    elif work_status == "Self-employed":
        return 80
    elif work_status == "Unemployed":
        return 30
    elif work_status == "Student":
        return 50
    elif work_status == "Retired":
        return 50
    else:
        return 60
    
def get_confidence_score(credit_score: float,  work_score: float, number_of_dependents : int) -> float:
    """
    Calculates the confidence score.

    Parameters:
    credit_score (float): The credit score.
    dti (float): The debt-to-income ratio.
    work_score (float): The work status score.

    Returns:
    float: The confidence score.
    """
    number_of_dependents = min(number_of_dependents, 10)
    return (credit_score*1 + work_score*0.5 + (10-number_of_dependents)*0.2) / 2
