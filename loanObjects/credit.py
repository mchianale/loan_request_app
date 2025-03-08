from pydantic import BaseModel, Field, model_validator
from typing import List
from enum import Enum
from loanObjects.utils import check_is_valid_date

class CreditTypeEnum(str, Enum):
    consumer = "Consumer Loan"
    mortgage = "Mortgage"
    auto = "Auto Loan"
    personal = "Personal Loan"
    business = "Business Loan"

class CreditStatusEnum(str, Enum):
    ongoing = "Ongoing"
    completed = "Completed"
    canceled = "Canceled"

class PaymentStatusEnum(str, Enum):
    paid_on_time = "Paid on time"
    paid_late = "Paid late"
    never_paid = "Never paid"

class PaymentHistory(BaseModel):
    payment_date: str = Field(..., description="Payment date in YYYY-MM-DD format")
    status: PaymentStatusEnum = Field(..., description="Payment status (restricted to allowed values)")

    @model_validator(mode="before")
    def pre_validate_data(cls, values: dict) -> dict:
        # check if start date is valid
        _ = check_is_valid_date(values.get("payment_date"))
        return values


class Credit(BaseModel):
    credit_type: CreditTypeEnum = Field(..., description="Type of credit (restricted to allowed credit types)")
    start_date: str = Field(..., description="Credit start date in YYYY-MM-DD format")
    amount: float = Field(..., description="Credit amount")
    duration_months: int = Field(..., description="Duration of the credit in months")
    annual_rate: float = Field(..., description="Annual interest rate (in percent)")
    status: CreditStatusEnum = Field(..., description="Current status of the credit")
    payment_history: List[PaymentHistory] = Field(..., description="History of payment records")

    class Config:
        extra = "forbid"  # Forbid any extra fields not defined in the model
        anystr_strip_whitespace = True

    @model_validator(mode="before")
    def pre_validate_data(cls, values: dict) -> dict:
        # check if start date is valid
        _ = check_is_valid_date(values.get("start_date"))

        # check amount is valid 
        amount = values.get('amount')
        if amount is None:
            raise ValueError("amount is required.")
        elif amount <= 0:
            raise ValueError("amount must be greater than 0.")
        
        # check duration_months is valid 
        duration_months = values.get('duration_months')
        if duration_months is None:
            raise ValueError("duration months is required.")
        elif duration_months <= 0:
            raise ValueError("duration months must be greater than 0.")
        
        # check annual_rate is valid 
        annual_rate = values.get('annual_rate')
        if annual_rate is None:
            raise ValueError("annual rate is required.")
        elif annual_rate <= 0:
            raise ValueError("annual rate must be greater than 0.")
        return values
class Credits(BaseModel):
    credits : List[Credit] = Field(default=[], description="list of all user's credit")

    class Config:
        extra = "forbid"  # Forbid extra fields not defined in the model
        anystr_strip_whitespace = True
    

"""# Example usage:
if __name__ == "__main__":
    example_credit_data = {
        "credit_type": "Consumer Loan",
        "start_date": "2020-01-15",
        "amount": 8000,
        "duration_months": 48,
        "annual_rate": 3.50,
        "status": "Ongoing",
        "payment_history": [
            {"date": "2020-02-15", "status": "Paid on time"},
            {"date": "2020-03-15", "status": "Paid on time"},
            {"date": "2020-04-15", "status": "Paid on time"}
        ],
        "incidents": [
            {
                "date": "2021-05-10",
                "description": "Payment delay of 10 days"
            }
        ]
    }
    
    credit = Credit(**example_credit_data)
    print(credit.json(indent=2))
"""

"""credit = Credit(**{
      "credit_type": "Consumer Loan",
      "start_date": "2020-01-15",
      "amount": 8000,
      "duration_months": 48,
      "annual_rate": 3.5,
      "status": "Ongoing",
      "payment_history": [
        {
          "payment_date": "2020-02-15",
          "status": "Paid on time"
        },
        {
          "payment_date": "2020-03-15",
          "status": "Paid on time"
        },
        {
          "payment_date": "2020-04-15",
          "status": "Paid on time"
        }
      ]
    })
c = Credits(**{"credits" : [credit]})
print(c.dict())"""

