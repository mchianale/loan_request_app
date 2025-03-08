import httpx
async def update_loan_request(
    loan_id : str,
    user_id : str,
    password: str,
    loan_status: str,
    loan_message: str,
    url: str,
    credit_check_response : dict = None,
    property_check_response: dict = None,
    repaymentSchedule: dict = None   
):
    # Construct the full JSON payload with all fields
    payload = {
        "user_id": user_id,
        "loan_id": loan_id,
        "password": password,
        "loan_status": loan_status,
        "loan_message": loan_message,
        "credit_check_response": credit_check_response,
        "property_check_response": property_check_response,
        "repaymentSchedule": repaymentSchedule
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=payload, headers=headers)
    
    return response