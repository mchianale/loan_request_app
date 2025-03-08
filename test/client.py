import httpx

BASE_URL = 'http://localhost:8000'

async def login(username : str, password : str, url : str = "http://localhost:8000/login"):
    payload = {
        "username" : username,
        "password" : password
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=payload, headers=headers)
        return response 


async def register(
    username: str,
    password: str,
    last_name: str,
    first_name: str,
    date_of_birth: str,  # Expecting a string in "YYYY-MM-DD" format
    address: str,
    marital_status: str,
    number_of_dependents: int,
    tax_residence: str,
    nationality: str,
    email: str,
    phone: str,
    work_status: str,
    gross_monthly_income: float,
    url: str = "http://localhost:8000/register"
):
    # Construct the full JSON payload with all fields
    payload = {
        "username": username,
        "password": password,
        "last_name": last_name,
        "first_name": first_name,
        "date_of_birth": date_of_birth,
        "address": address,
        "marital_status": marital_status,
        "number_of_dependents": number_of_dependents,
        "tax_residence": tax_residence,
        "nationality": nationality,
        "email": email,
        "phone": phone,
        "work_status": work_status,
        "gross_monthly_income": gross_monthly_income
    }
    
    headers = {"Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    
    return response

async def retrieve_user_information(access_token : str, url: str = "http://localhost:8000/retrieve_user_information"):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    
    return response

async def update_personal_data(
    access_token : str,
    last_name: str,
    first_name: str,
    date_of_birth: str,  # Expecting a string in "YYYY-MM-DD" format
    address: str,
    marital_status: str,
    number_of_dependents: int,
    tax_residence: str,
    nationality: str,
    email: str,
    phone: str,
    work_status: str,
    gross_monthly_income: float,
    url: str = "http://localhost:8000/update_personal_data"
):
    # Construct the full JSON payload with all fields
    payload = {
        "last_name": last_name,
        "first_name": first_name,
        "date_of_birth": date_of_birth,
        "address": address,
        "marital_status": marital_status,
        "number_of_dependents": number_of_dependents,
        "tax_residence": tax_residence,
        "nationality": nationality,
        "email": email,
        "phone": phone,
        "work_status": work_status,
        "gross_monthly_income": gross_monthly_income
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=payload, headers=headers)
    
    return response


async def update_credits_history(
    access_token : str,
    credits : list,
    url: str = "http://localhost:8000/update_credits_history"
):
    # Construct the full JSON payload with all fields
    payload = {
       "credits" : credits
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=payload, headers=headers)
    
    return response

async def retrieve_user_loans(access_token : str, url: str = "http://localhost:8000/retrieve_user_loans"):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    
    return response

async def create_loan_request(
    access_token: str,
    credit_type: str,
    loan_amount: float,
    duration_months: int,
    purpose: str,
    property_location: str,
    property_value: float,
    property_type: str,
    url: str = "http://localhost:8000/create_loan_request"
):
    """
    Create a new loan request with explicit arguments.

    :param access_token: User's JWT token for authentication.
    :param credit_type: Type of credit (Personal, Business, etc.).
    :param loan_amount: Requested loan amount.
    :param duration_months: Duration of the loan in months.
    :param purpose: Purpose of the loan.
    :param property_location: Location of the property.
    :param property_value: Value of the property.
    :param property_type: Type of property (House, Apartment, etc.).
    :param url: API endpoint for loan requests.
    :return: HTTP response from the API.
    """
    
    payload = {
        "credit_type": credit_type,   
        "loan_amount": loan_amount,
        "duration_months": duration_months,
        "purpose": purpose,
        "property_location": property_location,
        "property_value": property_value,
        "property_type": property_type 
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

    return response