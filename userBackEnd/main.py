from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uuid
import logging
from dotenv import load_dotenv
import os
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# connection to our mongodb 
from mongoClient import get_async_db_handle, get_sync_db_handle, init_client
# pydantic models
from baseModels import (
    HealthCheckResponse, 
    Token, 
    AuthResponse, 
    RegisterEntry,
    PersonalDataResponse,
    UserInformationResponse,
    CreditsDataResponse,
    AuthLoanUpdateEntry,
    LoanUpdateResponse
)
# security utils
from utils import (
            verify_password, 
            create_access_token, 
            hash_password, 
            validate_password, 
            validate_username, 
            decode_token, 
            get_current_date
        )
from password_manager import init_passwordManager, get_hashed_password
# kafka client
from kafkaClient import init_kafka_producer, get_kafka_producer, LogEntry
import asyncio
# loanObjetcs
from loanObjects import PersonalData, Credits, LoanRequestEntry, CreditCheckEntry, PropertyCheckEntry, Loan, LoanRequestResponse, FinalLoans
# CONSTANTS
load_dotenv()
LOAN_TOPIC= os.getenv("LOAN_TOPIC")
SERVICE_NAME="user-back-end"
security = HTTPBearer()

async def get_current_user(token: HTTPAuthorizationCredentials = Security(security), async_db=Depends(get_async_db_handle)):
    error = None
    try:
        user_id = decode_token(credentials=token.credentials)
        try:
            users_collection = async_db["users"]
            user = await users_collection.find_one({"_id": user_id})
            del user['password']
            if not user:
                error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
            else:
                return user
        except:
            error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    except Exception as e:
        error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return error

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Properly initialize the database on startup.
    """
    logging.info("Initializing MongoDB connection...")
    await init_client()  # Initialize DB only once at startup
    logging.info("MongoDB connection established successfully.")
    # init kafka producer
    init_kafka_producer()
    logging.info("Kafka producer retrieved successfully.")
    init_passwordManager()
    logging.info("password for ntoify is set.")
    yield  # This ensures FastAPI correctly waits for app shutdown


app = FastAPI(
    title="User Management API",
    description="API for user registration, login, and loan request handling using FastAPI and MongoDB.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# check if boths clients exists
@app.get("/health", summary="Health Check Endpoint", response_model=HealthCheckResponse, tags=["Health"])
def health_check(async_db=Depends(get_async_db_handle), sync_db=Depends(get_sync_db_handle))->HealthCheckResponse:
    """Checks the health of the API and database connection."""
    return HealthCheckResponse(status="healthy", async_db_connection="active" if async_db is not None else "inactive", sync_db_connection="active" if sync_db is not None else "inactive")

# AUTH - for normal users
@app.post(
    "/register", 
    summary="User Registration, update 'users' collection", 
    status_code=status.HTTP_201_CREATED, 
    response_model=AuthResponse, 
    tags=["Auth"]
)
async def register(registerEntry : RegisterEntry, sync_db=Depends(get_sync_db_handle), kafkaProducer=Depends(get_kafka_producer))->AuthResponse:
    error, authResponse  = None, None
    start_time = get_current_date()
    # validation
    username, password = registerEntry.username, registerEntry.password
    if not validate_username(username=username):
        error = HTTPException(status_code=400, detail="Username must be at least 3 characters long and must not contain spaces.")
    if not validate_password(password=password):
        error = HTTPException(status_code=400, detail="Password must be at least 6 characters long, contain at least one special character, and one number.")
    if error is None:
        try:
            # now manage the db
            users_collection = sync_db["users"]
            existing_user = users_collection.find_one({"username": username})
            if existing_user:
                error = HTTPException(status_code=400, detail="Username already exists")
            if error is None:
                hashed_password = hash_password(password=password)
                # create custom id, don't use Object id (not compatible with FastAPI)
                _id = str(uuid.uuid4())
                registerEntry.password = hashed_password
                user_data = {
                        "_id" : _id, 
                        "created_at": get_current_date()
                    } | registerEntry.dict() | {"credits" : []}
                users_collection.insert_one(
                    user_data
                )

                # create access_token
                access_token = create_access_token(data={"sub": _id})
                authResponse = AuthResponse(token=Token(access_token=access_token), message="User registered successfully")
        except HTTPException as e:
            error = e 
        except Exception as e:
            error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    # finish
    end_time = get_current_date()
    # log
    if error is None:
        logEntry: LogEntry = LogEntry(
            service=SERVICE_NAME, 
            endpoint='register',
            method='POST', 
            status=status.HTTP_201_CREATED, 
            message=authResponse.message,
            start_time=start_time,
            end_time=end_time,
            metadata={
                'user_id': _id
            }
            )
        asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
        return authResponse
    # error log
    logEntry: LogEntry = LogEntry(
            service=SERVICE_NAME, 
            endpoint='register',
            method='POST', 
            status=error.status_code, 
            message=error.detail,
            start_time=start_time,
            end_time=end_time,
            )
    asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
    raise error


@app.post("/login", summary="User Login", status_code=status.HTTP_201_CREATED, response_model=AuthResponse, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), async_db=Depends(get_async_db_handle), kafkaProducer=Depends(get_kafka_producer))->AuthResponse:
    error, authResponse  = None, None
    start_time = get_current_date()
    try:
        username, password = form_data.username, form_data.password
        # credentials check
        users_collection = async_db["users"]
        user = await users_collection.find_one({"username": username})
        if not user or not verify_password(password, user["password"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        # create access_token
        access_token = create_access_token(data={"sub": user['_id']})
        authResponse =  AuthResponse(token=Token(access_token=access_token), message="User logged in successfully")
    except HTTPException as e:
        error = e 
    except Exception as e:
        error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    # finish
    end_time = get_current_date()
    # log
    if error is None:
        logEntry: LogEntry = LogEntry(
            service=SERVICE_NAME, 
            endpoint='login',
            method='POST', 
            status=status.HTTP_201_CREATED, 
            message=authResponse.message,
            start_time=start_time,
            end_time=end_time,
            metadata={
                'user_id': user['_id']
            }
            )
        asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
        return authResponse
    # error log
    logEntry: LogEntry = LogEntry(
            service=SERVICE_NAME, 
            endpoint='login',
            method='POST', 
            status=error.status_code, 
            message=error.detail,
            start_time=start_time,
            end_time=end_time,
            )
    asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
    raise error
   

# test
@app.post("/test", summary="Test Endpoint", tags=["Auth"])
async def test(async_db=Depends(get_async_db_handle)):
    users_collection = async_db["users"]
    users = await users_collection.find().to_list(length=100)  # Fetch up to 100 users
    return users

@app.post("/test2", summary="Test 2 Endpoint", tags=["Auth"])
async def test2(async_db=Depends(get_async_db_handle)):
    users_collection = async_db["loans"]
    users = await users_collection.find().to_list(length=100)  # Fetch up to 100 users
    return users

# USER
# Endpoint to retrieve user info
@app.get(
    "/retrieve_user_information",
    summary="get main user's informations",
    status_code=status.HTTP_200_OK,
    response_model=UserInformationResponse,
    tags=["User"]
)
async def retrieve_user_information(
    current_user=Depends(get_current_user),
    kafkaProducer=Depends(get_kafka_producer)
) ->  UserInformationResponse:
    error, response = None, None
    start_time = get_current_date()
    if not isinstance(current_user, HTTPException):
        _id = current_user["_id"]
        del current_user["_id"]
        del current_user["created_at"]
        response = UserInformationResponse(**current_user)
    else:
        error = current_user
    end_time = get_current_date()
    if error is None:
        logEntry = LogEntry(
            service=SERVICE_NAME,
            endpoint="retrieve_user_information",
            method="GET",
            status=status.HTTP_200_OK,
            message=response.message,
            start_time=start_time,
            end_time=end_time,
            metadata={"user_id": _id}
        )
        asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
        return response
    logEntry = LogEntry(
        service=SERVICE_NAME,
        endpoint="retrieve_user_information",
        method="GET",
        status=error.status_code,
        message=error.detail,
        start_time=start_time,
        end_time=end_time,
    )
    asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
    raise error

# Endpoint to add a new credit history 
@app.put(
    "/update_credits_history",
    summary="Update credits history by adding a new credit",
    status_code=status.HTTP_200_OK,
    response_model=CreditsDataResponse,
    tags=["User"]
)
async def update_credits_history(
    new_credits: Credits,
    async_db=Depends(get_async_db_handle),
    current_user=Depends(get_current_user),
    kafkaProducer=Depends(get_kafka_producer)
) -> CreditsDataResponse:
    error, response = None, None
    start_time = get_current_date()
    if not isinstance(current_user, HTTPException):
        try:
            users_collection = async_db["users"]
            update_result = await users_collection.update_one(
                {"_id": current_user["_id"]},
                {"$set": new_credits.dict()}
            )
            if update_result.matched_count != 1:
                error = HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found or no data modified"
                )
            elif update_result.modified_count != 1:
                response = CreditsDataResponse(message="There have been no changes made.")
            else:
                response = CreditsDataResponse()
        except HTTPException as e:
            error = e
        except Exception as e:
            if error is None:
                error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    else:
        error = current_user

    end_time = get_current_date()
    if error is None:
        logEntry = LogEntry(
            service=SERVICE_NAME,
            endpoint="update_credits_history",
            method="PUT",
            status=status.HTTP_200_OK,
            message=response.message,
            start_time=start_time,
            end_time=end_time,
            metadata={"user_id": current_user["_id"]}
        )
        asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
        return response
    logEntry = LogEntry(
        service=SERVICE_NAME,
        endpoint="update_credits_history",
        method="PUT",
        status=error.status_code,
        message=error.detail,
        start_time=start_time,
        end_time=end_time,
    )
    asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
    raise error

# Endpoint to update personal data
@app.put(
    "/update_personal_data",
    summary="Update Personal Data",
    status_code=status.HTTP_200_OK,
    response_model=PersonalDataResponse,
    tags=["User"]
)
async def update_personal_data(
    personal_data: PersonalData,
    async_db=Depends(get_async_db_handle),
    current_user=Depends(get_current_user),
    kafkaProducer=Depends(get_kafka_producer)
) -> PersonalDataResponse:
    error, response = None, None
    start_time = get_current_date()
    if not isinstance(current_user, HTTPException):
        try:
            users_collection = async_db["users"]
            update_result = await users_collection.update_one(
                {"_id": current_user["_id"]},
                {"$set": personal_data.dict()}
            )
            if update_result.matched_count != 1:
                error = HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found or no data modified"
                )
            elif update_result.modified_count != 1:
                response = PersonalDataResponse(message="There have been no changes made.")
            else:
                response = PersonalDataResponse()
        except HTTPException as e:
            error = e
        except Exception as e:
            if error is None:
                error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    else:
        error = current_user

    end_time = get_current_date()
    if error is None:
        logEntry = LogEntry(
            service=SERVICE_NAME,
            endpoint="update_personal_data",
            method="PUT",
            status=status.HTTP_200_OK,
            message=response.message,
            start_time=start_time,
            end_time=end_time,
            metadata={"user_id": current_user["_id"]}
        )
        asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
        return response
    logEntry = LogEntry(
        service=SERVICE_NAME,
        endpoint="update_personal_data",
        method="PUT",
        status=error.status_code,
        message=error.detail,
        start_time=start_time,
        end_time=end_time,
    )
    asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
    raise error



# loans management
@app.post(
    "/create_loan_request", 
    summary="Create Loan Request", 
    status_code=status.HTTP_201_CREATED, 
    response_model=LoanRequestResponse, 
    tags=["Loans"]
)
async def create_loan_request(request : LoanRequestEntry, async_db=Depends(get_async_db_handle), output=Depends(get_current_user), kafkaProducer=Depends(get_kafka_producer))->LoanRequestResponse:
    error, loanResponse = None, None
    start_time = get_current_date()

    if not isinstance(output, HTTPException):
        try:
            # create new loan
            loan_id = str(uuid.uuid4())
            loan_dict = request.dict() | {
                "loan_id": loan_id, 
                "user_id": output["_id"],
                "created_at": get_current_date().isoformat(),
                "loan_status": "Pending", 
                "loan_message": "Loan request created successfully"}
            loan = Loan(**loan_dict)
            # create info for credit check service
            credit_check_entry = CreditCheckEntry(
                loan_id=loan_id,
                user_id=output["_id"],
                # loan info
                loan_amount=request.loan_amount,
                duration_months=request.duration_months,
                # user info 
                date_of_birth=output["date_of_birth"],
                gross_monthly_income=output["gross_monthly_income"],
                number_of_dependents=output["number_of_dependents"],
                work_status=output["work_status"],
                user_credits=output["credits"],
            )
            # create info for property check service
            property_check_entry = PropertyCheckEntry(
                loan_amount=request.loan_amount,
                property_value=request.property_value
            )
            loan_collection = async_db["loans"]
            loan_dict["_id"] = loan_id
            del loan_dict["loan_id"]
            await loan_collection.insert_one(loan_dict)

            loanResponse = LoanRequestResponse(
                            loan=loan, 
                            credit_check_entry=credit_check_entry,
                            property_check_entry=property_check_entry
                        )
            # produced a message for celery
            asyncio.create_task(kafkaProducer.send_message_async(content=loanResponse.dict(), kafka_topic=LOAN_TOPIC))
        except HTTPException as e:
            error = e    
        except Exception as e:
            if error is None:
                error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")           
    else:
        error = output
  
    # finish
    end_time = get_current_date()
    # log
    if error is None:
        logEntry: LogEntry = LogEntry(
            service=SERVICE_NAME, 
            endpoint='create_loan_request',
            method='POST', 
            status=status.HTTP_201_CREATED, 
            message=loanResponse.loan.loan_message,
            start_time=start_time,
            end_time=end_time,
            metadata={
                'loan_id': loan_dict["_id"],
                'user_id': loan_dict['user_id'],
                'status' : "Pending"
            }
            )
        asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
        return loanResponse
    # error log
    logEntry: LogEntry = LogEntry(
            service=SERVICE_NAME, 
            endpoint='create_loan_request',
            method='POST', 
            status=error.status_code, 
            message=error.detail,
            start_time=start_time,
            end_time=end_time,
            )
    asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
    raise error

# update a loan request
@app.put(
    "/update_loan_request",
    summary="update a loan request (only admin can do it)", 
    status_code=status.HTTP_201_CREATED, 
    response_model=LoanUpdateResponse, 
    tags=["Loan"]
)
async def update_loan_request(authLoanUpdateEntry: AuthLoanUpdateEntry, hashed_password: str = Depends(get_hashed_password), kafkaProducer=Depends(get_kafka_producer), async_db=Depends(get_async_db_handle))->LoanUpdateResponse:
    error, response = None, None
    start_time = get_current_date()
    try:
        # credentials check
        password = authLoanUpdateEntry.password
        if not verify_password(password, hashed_password):
            error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        else:
            loan_dict = authLoanUpdateEntry.dict()
            loan_dict["_id"] = loan_dict["loan_id"]
            del loan_dict["loan_id"]
            del loan_dict["password"]

            loans_collection = async_db["loans"]
            update_result = await loans_collection.update_one(
                {"_id": loan_dict["_id"]},
                {"$set": loan_dict}
            )
            if update_result.matched_count != 1:
                error = HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found or no data modified"
                )
            elif update_result.modified_count != 1:
                response = LoanUpdateResponse(message="There have been no changes made.")
            else:
                response = LoanUpdateResponse()
    except HTTPException as e:
        error = e    
    except Exception as e:
        if error is None:
            error = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")   
    # finish
    end_time = get_current_date()
    # log
    if error is None:
        logEntry: LogEntry = LogEntry(
            service=SERVICE_NAME, 
            endpoint='update_loan_request',
            method='PUT', 
            status=status.HTTP_201_CREATED, 
            message=response.message,
            start_time=start_time,
            end_time=end_time,
            metadata={
                'loan_id': loan_dict["_id"],
                'user_id': loan_dict['user_id']
            }
            )
        asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
        return response
    # error log
    logEntry: LogEntry = LogEntry(
            service=SERVICE_NAME, 
            endpoint='update_loan_request',
            method='PUT', 
            status=error.status_code, 
            message=error.detail,
            start_time=start_time,
            end_time=end_time,
            )
    asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
    raise error   

@app.get(
    "/retrieve_user_loans",
    summary="get loans of a user",
    status_code=status.HTTP_200_OK,
    response_model=FinalLoans,
    tags=["Loan"]
)
async def retrieve_user_loans(
    current_user=Depends(get_current_user),
    kafkaProducer=Depends(get_kafka_producer),
    async_db=Depends(get_async_db_handle)
) ->  FinalLoans:
    error, response = None, None
    start_time = get_current_date()
    if not isinstance(current_user, HTTPException):
        user_id = current_user["_id"]
        loans_collection = async_db["loans"]
        loans = await loans_collection.find({"user_id": user_id}).to_list()
        response = FinalLoans(loans=loans)
    else:
        error = current_user
    end_time = get_current_date()
    if error is None:
        logEntry = LogEntry(
            service=SERVICE_NAME,
            endpoint="retrieve_user_loans",
            method="GET",
            status=status.HTTP_200_OK,
            message='successfully retrieve all loans',
            start_time=start_time,
            end_time=end_time,
            metadata={"user_id": user_id}
        )
        asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
        return response
    logEntry = LogEntry(
        service=SERVICE_NAME,
        endpoint="retrieve_user_loans",
        method="GET",
        status=error.status_code,
        message=error.detail,
        start_time=start_time,
        end_time=end_time,
    )
    asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
    raise error