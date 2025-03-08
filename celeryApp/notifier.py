import httpx
async def notify(
    loan_id : str,
    user_id : str,
    password: str,
    loan_status: str,
    finish: bool,
    message: str,
    url: str
):
    # Construct the full JSON payload with all fields
    payload = {
        "user_id": user_id,
        "loan_id": loan_id,
        "password": password,
        "loan_status": loan_status,
        "finish": finish,
        "message": message
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    
    return response