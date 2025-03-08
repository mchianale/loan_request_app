from fastapi import FastAPI, HTTPException, status 
from baseModels import HealthCheckResponse
# loanObjetcs
from loanObjects import PropertyCheckEntry, PropertyCheckResponse, LtvScoreEnum
# utils
from utils import get_loan_to_value, get_loan_value_score

 
app = FastAPI(
    title="Property Check API",
    description="API to evaluate property for the loan request.",
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
    "/evaluate_property", 
    summary="Evaluate property Endpoint",
    status_code=status.HTTP_201_CREATED, 
    tags=["Property"],
    response_model=PropertyCheckResponse, 
)
def evaluate_property(property_entry : PropertyCheckEntry)->PropertyCheckResponse:
    error, propertyCheckResponse = None, None
    try:  
        status_ = "Approved" 
        message_ = "Property evaluation approved"
        property_entry.loan_amount
        property_entry.property_value
        # get loan to value
        ltv = get_loan_to_value(property_entry.loan_amount, property_entry.property_value)
        ltv_score =  get_loan_value_score(ltv)
        if ltv_score == LtvScoreEnum.risky:
            status_ = "Denied"
            message_ = "Loan-to-Value ratio too high, this property project is risky."
        else:
            message_ += f", this property project seems {ltv_score.value}."
     
        # create response
        propertyCheckResponse = PropertyCheckResponse(
            ltv=ltv,
            ltv_score=ltv_score,
            status=status_,
            message=message_
        )  
    except HTTPException as e:
        error = e    
    except Exception as e:
        if error is None:
            error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")           

    if error is None:
        return propertyCheckResponse
    raise error
