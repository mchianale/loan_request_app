from fastapi import FastAPI, HTTPException, status 
from baseModels import HealthCheckResponse
from utils import generate_repayment_schedule
# loanObjetcs
from loanObjects import LoanStatusEnum, CreditCheckResponse, PropertyCheckResponse, DecisionEntry, DecisionResponse, RepaymentSchedule
# utils
N_DAYS_START = 20
 
app = FastAPI(
    title="Decison loan API",
    description="API to consitute the final decison of the loan request based on property and credit evaluations, create also a repayment schedule.",
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
    "/loan_decision", 
    summary="Consitute the final decison of the loan request based on property and credit evaluations, create also a repayment schedule.",
    status_code=status.HTTP_201_CREATED, 
    tags=["Loan"],
    response_model=DecisionResponse, 
)
def loan_decision(decision_entry: DecisionEntry)->DecisionResponse:
    error, decisionResponse = None, None
    
    try:  
        status_ = "Approved" 
        message_ = f"Decision of the loan request:\n1. Credit & Profile Evaluation:\n- {decision_entry.credit_check_response.message} ({decision_entry.credit_check_response.status})\n\n2. Property Evaluation:\n- {decision_entry.property_check_response.message} ({decision_entry.property_check_response.status})"
        if decision_entry.credit_check_response.status.value == LoanStatusEnum.denied or decision_entry.property_check_response.status.value == LoanStatusEnum.denied:
            status_ = LoanStatusEnum.denied
            message_ += f"\nSorry your loan request is {status_}, see you soon."
            # don't create repayment schedule
            decisionResponse = DecisionResponse(
                message=message_,
                status=status_,
                credit_check_response=decision_entry.credit_check_response,
                property_check_response=decision_entry.property_check_response
            )
        else:
            status_ = LoanStatusEnum.approved
            message_ += f"\nYour loan request is {status_}, youn will be contacted soon."
            # create a repayment schedule
            repaymentSchedule: RepaymentSchedule = generate_repayment_schedule(
                duration_months=decision_entry.credit_check_response.duration_months,
                monthly_payment=decision_entry.credit_check_response.monthly_payment,
                start_offset_days=N_DAYS_START
            )
            decisionResponse = DecisionResponse(
                message=message_,
                status=status_,
                credit_check_response=decision_entry.credit_check_response,
                property_check_response=decision_entry.property_check_response,
                repaymentSchedule=repaymentSchedule
            )
      
    except HTTPException as e:
        error = e    
    except Exception as e:
        if error is None:
            error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")           

    if error is None:
        return decisionResponse
    raise error
