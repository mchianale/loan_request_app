from pydantic import BaseModel, Field
from loanObjects import LoanNotificationMessage, LoanStatusEnum
# health
class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="The current status of the API (e.g., healthy, degraded)")

class NotifyResponse(BaseModel):
    loan_id : str = Field(..., description="Unique id of the loan request")
    loan_status : LoanStatusEnum = Field(..., description="Status of the loan request")
    finish : bool = Field(default=False, description="Tell if the loan request evaluation is finish or not.")
    message : str = Field(..., description="Return message response, depends of auth methods (login or register)")

class AuthLoanNotificationMessage(LoanNotificationMessage):
    password : str = Field(..., description="Admin password")
