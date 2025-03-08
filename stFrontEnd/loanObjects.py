from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class WorkStatusEnum(str, Enum):
    employed = "Employed"
    self_employed = "Self-employed"
    unemployed = "Unemployed"
    student = "Student"
    retired = "Retired"
    other = "Other"
def get_work_status_values()->list:
    return [v.value for v in list(WorkStatusEnum)]

class MaritalStatusEnum(str, Enum):
    married = "Married",
    single = "Single"
def get_values_marital_status()->list:
    return [v.value for v in list(MaritalStatusEnum)]

class PersonalData(BaseModel):
    last_name: str = Field(...,min_length=1, description="Last name of the person")
    first_name: str = Field(...,min_length=1, description="First name of the person")
    date_of_birth: str = Field(..., description="Birth date in YYYY-MM-DD format")
    address: str = Field(...,min_length=1, description="Full address including street, postal code, city, and country")
    marital_status: MaritalStatusEnum = Field(...,min_length=1, description="Marital status (e.g., Married, Single)")
    tax_residence: str = Field(...,min_length=1, description="Country of tax residence")
    nationality: str = Field(...,min_length=1, description="Nationality of the person")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number, including country code if applicable")
    # use to score profile
    number_of_dependents: int = Field(..., description="Number of dependents")
    gross_monthly_income : float = Field(..., description="Gross monthly income in USD")
    work_status: WorkStatusEnum = Field(..., description="Work status (e.g., Employed, Self-employed, Unemployed, Student, Retired, Other)")

    class Config:
        extra = "forbid"  # Forbid any extra fields not defined in the model
        anystr_strip_whitespace = True

# Credit history
class CreditTypeEnum(str, Enum):
    consumer = "Consumer Loan"
    mortgage = "Mortgage"
    auto = "Auto Loan"
    personal = "Personal Loan"
    business = "Business Loan"
def get_values_credit_type()->list:
    return [v.value for v in list(CreditTypeEnum)]


class CreditStatusEnum(str, Enum):
    ongoing = "Ongoing"
    completed = "Completed"
    canceled = "Canceled"
def get_values_credit_status()->list:
    return [v.value for v in list(CreditStatusEnum)]

class PaymentStatusEnum(str, Enum):
    paid_on_time = "Paid on time"
    paid_late = "Paid late"
    never_paid = "Never paid"
def get_values_payment_status()->list:
    return [v.value for v in list(PaymentStatusEnum)]

class PropertyTypeEnum(str, Enum):
    house = "House"
    apartment = "Apartment"
    land = "Land"
    commercial = "Commercial"
    other = "Other"
def get_values_property_type():
    return [v.value for v in list(PropertyTypeEnum)]

class PaymentHistory(BaseModel):
    payment_date: str = Field(..., description="Payment date in YYYY-MM-DD format")
    status: PaymentStatusEnum = Field(..., description="Payment status (restricted to allowed values)")


class Credit(BaseModel):
    credit_type: CreditTypeEnum = Field(..., description="Type of credit (restricted to allowed credit types)")
    start_date: str = Field(..., description="Credit start date in YYYY-MM-DD format")
    amount: float = Field(..., description="Credit amount")
    duration_months: float = Field(..., description="Duration of the credit in months")
    annual_rate: float = Field(..., description="Annual interest rate (in percent)")
    status: CreditStatusEnum = Field(..., description="Current status of the credit")
    payment_history: List[PaymentHistory] = Field(..., description="History of payment records")

    class Config:
        extra = "forbid"  # Forbid any extra fields not defined in the model
        anystr_strip_whitespace = True

    
class Credits(BaseModel):
    credits : List[Credit] = Field(default=[], description="list of all user's credit")

    class Config:
        extra = "forbid"  # Forbid extra fields not defined in the model
        anystr_strip_whitespace = True
    

# personal user information
class UserInformation(PersonalData):
    username : str = Field(..., description="unique username of the user, can't contain space.")
    credits : list = Field(..., description="Credits history of the user")
    class Config:
        extra = "forbid"  # Forbid any extra fields not defined in the model
        anystr_strip_whitespace = True
