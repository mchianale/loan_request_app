from pydantic import BaseModel, Field, EmailStr, model_validator
from enum import Enum
from datetime import date
import re
from loanObjects.utils import check_is_valid_date

class WorkStatusEnum(str, Enum):
    employed = "Employed"
    self_employed = "Self-employed"
    unemployed = "Unemployed"
    student = "Student"
    retired = "Retired"
    other = "Other"

class MaritalStatusEnum(str, Enum):
    married = "Married",
    single = "Single"

class PersonalData(BaseModel):
    last_name: str = Field(...,min_length=1, description="Last name of the person")
    first_name: str = Field(...,min_length=1, description="First name of the person")
    date_of_birth: str = Field(..., description="Birth date in YYYY-MM-DD format")
    address: str = Field(...,min_length=1, description="Full address including street, postal code, city, and country")
    marital_status: MaritalStatusEnum = Field(...,min_length=1, description="Marital status (e.g., Married, Single)")
    tax_residence: str = Field(...,min_length=1, description="Country of tax residence")
    nationality: str = Field(...,min_length=1, description="Nationality of the person")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number, including country code if applicable")
    # use to score profile
    number_of_dependents: int = Field(..., description="Number of dependents")
    gross_monthly_income : float = Field(..., description="Gross monthly income in USD")
    work_status: WorkStatusEnum = Field(..., description="Work status (e.g., Employed, Self-employed, Unemployed, Student, Retired, Other)")

    class Config:
        extra = "forbid"  # Forbid any extra fields not defined in the model
        anystr_strip_whitespace = True

    @model_validator(mode="before")
    def pre_validate_data(cls, values: dict) -> dict:
        # capitalize firstname and lastname
        firstname, lastname = values.get('first_name'), values.get('last_name')
        firstname = " ".join([c[0].upper() + c[1:].lower() for c in firstname.split()])
        lastname = " ".join([c[0].upper() + c[1:].lower() for c in lastname.split()])
        values['first_name'] = firstname
        values['last_name'] = lastname
        # Validate date_of_birth format (YYYY-MM-DD) and check if user is at least 18.
        dob = values.get("date_of_birth")
        parsed_dob = check_is_valid_date(dob)
        
        # Check if the user is at least 18 years old.
        today = date.today()
        age = today.year - parsed_dob.year - ((today.month, today.day) < (parsed_dob.month, parsed_dob.day))
        if age < 18:
            raise ValueError("User must be at least 18 years old.")
        
        # Validate that number_of_dependents is a non-negative integer.
        num_dep = values.get("number_of_dependents")
        if num_dep is None:
            raise ValueError("number of dependents is required.")
        if not isinstance(num_dep, int) or num_dep < 0:
            raise ValueError("number of dependents must be a non-negative integer.")
        gms = values.get("gross_monthly_income")
        if gms is None:
            raise ValueError("gross monthly income is required.")
        if gms < 0:
            raise ValueError("gross monthly income must be a non-negative integer.")
        # Validate phone format: only digits with an optional leading plus sign
        phone = values.get("phone")
        if not phone:
            raise ValueError("phone is required.")
        if not re.fullmatch(r"\+?\d+", phone):
            raise ValueError("phone must contain only digits and an optional leading plus sign.")

        return values
