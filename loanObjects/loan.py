from pydantic import BaseModel, Field, model_validator
from enum import Enum
from credit import CreditTypeEnum, Credit
from typing import List, Optional
from personalData import WorkStatusEnum
from loanObjects.utils import check_is_valid_date

class LoanStatusEnum(str, Enum):
    pending = "Pending"
    cancelled = "Cancelled"
    approved = "Approved"
    denied = "Denied"

class PropertyTypeEnum(str, Enum):
    house = "House"
    apartment = "Apartment"
    land = "Land"
    commercial = "Commercial"
    other = "Other"

class LtvScoreEnum(str, Enum):
    excellent = "Excellent"
    good = "Good"
    fair = "Fair"
    risky = "Risky"

class LoanRequestEntry(BaseModel):
    credit_type: CreditTypeEnum = Field(..., description="Type of credit (restricted to allowed credit types)")
    loan_amount: float = Field(..., description="Amount of the loan requested")
    duration_months: int = Field(..., description="Duration of the loan in months")
    purpose: str = Field(..., description="Purpose of the loan")
    # property 
    property_location: str = Field(..., description="Location of the property")
    property_value: float = Field(..., description="Value of the property")
    property_type: PropertyTypeEnum = Field(..., description="Type of the property")

    class Config:
        extra = "forbid"  # Forbid any extra fields not defined in the model
        anystr_strip_whitespace = True

    @model_validator(mode="before")
    def pre_validate_data(cls, values: dict) -> dict:
        loan_amount = values.get('loan_amount')
        if loan_amount is None:
            raise ValueError("loan amount is required.")
        elif loan_amount <= 0:
            raise ValueError("loan amount must be greater than 0.")

        duration_months = values.get('duration_months')
        if duration_months is None:
            raise ValueError("duration months is required.")
        elif duration_months <= 0:
            raise ValueError("duration months must be greater than 0.")
        
        property_value = values.get('property_value')
        if property_value is None:
            raise ValueError("property value is required.")
        elif property_value <= 0:
            raise ValueError("property value must be greater than 0.")
        return values
    

# for credit check service
class CreditCheckEntry(BaseModel):
    # to compute monthly payment
    loan_amount: float = Field(..., description="Amount of the loan requested")
    duration_months: int = Field(..., description="Duration of the loan in months")
    # to compute Debt-to-Income (DTI) ou Taux d’Endettement
    gross_monthly_income : float = Field(..., description="Gross monthly income in USD")
    user_credits: List[Credit]  = Field(..., description="List of all user's credit (history)")
    # to compute profile score
    date_of_birth: str = Field(..., description="Birth date in YYYY-MM-DD format")
    number_of_dependents: int = Field(..., description="Number of dependents")
    work_status: WorkStatusEnum = Field(..., description="Work status (e.g., Employed, Self-employed, Unemployed, Student, Retired, Other)")
    # normally all already validated 

class CreditCheckResponse(BaseModel):
    monthly_payment : float = Field(..., description="Monthly payment")
    monthly_rate : float = Field(..., description="Monthly rate")
    dti : float = Field(..., description="Debt-to-Income (DTI) ratio")
    confidence_score : float = Field(..., description="Credit score")
    duration_months: int = Field(..., description="Duration of the loan in months")
    status : LoanStatusEnum = Field(..., description="Status of the credit check (e.g., Approved, Denied)")
    message : str = Field(..., description="Message explaining the status of the credit check")

class PropertyCheckEntry(BaseModel):
    loan_amount: float = Field(..., description="Amount of the loan requested")
    property_value: float = Field(..., description="Value of the property")

class PropertyCheckResponse(BaseModel):
    ltv : float = Field(..., description="Loan-to-Value (LTV) ratio")
    ltv_score : LtvScoreEnum = Field(..., description="range score based on Loan to Value")
    status : LoanStatusEnum = Field(..., description="Status of the property check (e.g., Approved, Denied)")
    message : str = Field(..., description="Message explaining the status of the property check")

class RepaymentEvent(BaseModel):
    payment_date: str = Field(..., description="Payment date in YYYY-MM-DD format")
    amount: float = Field(..., description="Amount to pay")

    @model_validator(mode="before")
    def pre_validate_data(cls, values: dict) -> dict:
        # check if start date is valid
        _ = check_is_valid_date(values.get("payment_date"))
        return values
    
class RepaymentSchedule(BaseModel):
    start_date: str = Field(..., description="Payment date in YYYY-MM-DD format")
    repaymentEvent: List[RepaymentEvent] = Field(..., description="payment events which consistute a schedule for a specific loan request")

    @model_validator(mode="before")
    def pre_validate_data(cls, values: dict) -> dict:
        # check if start date is valid
        _ = check_is_valid_date(values.get("start_date"))
        return values
    
class DecisionEntry(BaseModel):
    credit_check_response : CreditCheckResponse = Field(..., description="Decision of credit evaluation.")
    property_check_response : PropertyCheckResponse = Field(..., description="Decision of property evaluation.")

class DecisionResponse(BaseModel):
    message: str = Field(..., description="Resume message based on evaluations.")
    credit_check_response : CreditCheckResponse = Field(..., description="Decision of credit evaluation.")
    property_check_response : PropertyCheckResponse = Field(..., description="Decision of property evaluation.")
    repaymentSchedule : Optional[RepaymentSchedule] = Field(..., description="Repayment Schedule")
    status : LoanStatusEnum = Field(..., description="Final status (e.g., Approved, Denied)")

class Loan(LoanRequestEntry):
    loan_id : str = Field(..., description="Unique id of the loan request")
    user_id : str = Field(..., description="Unique id of the user")
    loan_status : LoanStatusEnum = Field(..., description="Status of the loan request")
    loan_message : str = Field(default="Loan request created successfully", description="Response message indicating loan request creation status.")
    created_at : str = Field(..., description="Date of the loan request creation")

# main will be user by user back end to return a new loan and catch by celery from kafka
class LoanRequestResponse(BaseModel):
    loan : Loan = Field(..., description="Loan main informations")
    credit_check_entry : CreditCheckEntry = Field(..., description="Credit check entry for credit check (client profil) evaluation")
    property_check_entry : PropertyCheckEntry = Field(..., description="Property check entry for property evaluation")

class LoanUpdateEntry(BaseModel):
    loan_id : str = Field(..., description="Unique id of the loan request")
    user_id : str = Field(..., description="Unique id of the user")
    loan_status : LoanStatusEnum = Field(..., description="Status of the loan request")
    loan_message : str = Field(default="Loan request created successfully", description="Response message indicating loan request creation status.")
    credit_check_response : Optional[dict] = Field(default=None, description="Decision of credit evaluation.")
    property_check_response : Optional[dict] = Field(default=None, description="Decision of property evaluation.")
    repaymentSchedule : Optional[dict] = Field(default=None, description="Repayment Schedule")


class FinalLoans(BaseModel):
    loans : List[dict] = Field(..., description="list of loans") 

class LoanNotificationMessage(BaseModel):
    loan_id : str = Field(..., description="Unique id of the loan request")
    user_id : str = Field(..., description="Unique id of the user")
    loan_status : LoanStatusEnum = Field(..., description="Status of the loan request")
    finish : bool = Field(default=False, description="Tell if the loan request evaluation is finish or not.")
    message: str = Field(..., description="Resume message based on evaluations.")
