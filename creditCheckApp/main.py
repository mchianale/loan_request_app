from fastapi import FastAPI, HTTPException, status 
from baseModels import HealthCheckResponse
# loanObjetcs
from loanObjects import CreditCheckEntry, CreditCheckResponse
# utils
from utils import get_monthly_rate, get_monthly_payment, evaluate_user_credits, get_dti, get_work_score, get_confidence_score

# CONSTANTS
ANNUAL_RATE = 3.24
MONTHLY_RATE = get_monthly_rate(ANNUAL_RATE)

 
app = FastAPI(
    title="Credit Check API",
    description="API to evaluate profile and credit score of a user.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# check if boths clients exists
@app.get("/health", summary="Health Check Endpoint", response_model=HealthCheckResponse, tags=["Health"])
def health_check()->HealthCheckResponse:
    """Checks the health of the API and database connection."""
    return HealthCheckResponse(status="healthy")

@app.post(
    "/evaluate_credit", 
    summary="Evaluate Credit Endpoint",
    status_code=status.HTTP_201_CREATED, 
    tags=["Credit"],
    response_model=CreditCheckResponse, 
)
def evaluate_credit(credit_entry : CreditCheckEntry)->CreditCheckResponse:
    error, creditCheckResponse = None, None
    try:  
        status_ = "Approved" 
        message_ = "Credit evaluation approved"
        # get monthly payment
        monthly_payment = get_monthly_payment(credit_entry.loan_amount, credit_entry.duration_months, MONTHLY_RATE)
        # evaluate credit history
        credits_eval = evaluate_user_credits(credit_entry.user_credits, credit_entry.date_of_birth)
        credit_score = credits_eval["credit_score"]
        all_monthly_payment = credits_eval["all_monthly_payment"]
        # dti 
        dti = get_dti(credit_entry.gross_monthly_income, monthly_payment+all_monthly_payment)
        # work score
        work_score = get_work_score(credit_entry.work_status)
        # confidence score
        confidence_score = get_confidence_score(credit_score, work_score, credit_entry.number_of_dependents)
        if dti > 40:
            status_ = "Denied"
            message_ = "Debt-to-Income ratio too high, credit check denied."
        elif confidence_score < 30:
            status_ = "Denied"
            message_ = "Low confidence score, credit check denied."
        # create response
        creditCheckResponse = CreditCheckResponse(
            monthly_payment=monthly_payment,
            monthly_rate=MONTHLY_RATE,
            dti=dti,
            confidence_score=confidence_score,
            duration_months=credit_entry.duration_months,
            status=status_,
            message=message_
        )  
    except HTTPException as e:
        error = e    
    except Exception as e:
        if error is None:
            error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")           

    if error is None:
        return creditCheckResponse
    raise error
