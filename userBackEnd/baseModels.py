from pydantic import BaseModel, Field
from loanObjects import PersonalData, LoanUpdateEntry
# health
class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="The current status of the API (e.g., healthy, degraded)")
    async_db_connection: str = Field(..., description="Indicates whether the async database connection is active or inactive")
    sync_db_connection: str = Field(..., description="Indicates whether the sync database connection is active or inactive")

# authentification
class Token(BaseModel):
    access_token : str = Field(..., description="Access token to manage user session and verification")
    token_type: str = Field(default="bearer", description="Type of token")

class AuthResponse(BaseModel):
    message : str = Field(..., description="Return message response, depends of auth methods (login or register)")
    token : Token 

class RegisterEntry(PersonalData):
    username : str = Field(..., description="unique username of the user, can't contain space.")
    password : str = Field(..., description="password for account")

# Users
class PersonalDataResponse(BaseModel):
    message: str = Field(default="Personal data updated successfully", description="Response message indicating update status.")

# Users
class CreditsDataResponse(BaseModel):
    message: str = Field(default="Credits data updated successfully", description="Response message indicating update status.")

class UserInformationResponse(PersonalData):
    username : str = Field(..., description="unique username of the user, can't contain space.")
    credits : list = Field(..., description="Credits history of the user")
    message: str = Field(default="Successfully retrieve all informations", description="Response message indicating retreive informations worked.")

class AuthLoanUpdateEntry(LoanUpdateEntry):
    password : str = Field(..., description="Admin password")

class LoanUpdateResponse(BaseModel):
    message: str = Field(default="Loan data updated successfully", description="Response message indicating update status.")
