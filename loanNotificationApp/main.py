from fastapi import FastAPI, Depends, HTTPException, status,  WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from baseModels import HealthCheckResponse, NotifyResponse, AuthLoanNotificationMessage
from utils import verify_password, get_current_date, decode_token
from password_manager import init_passwordManager, get_hashed_password
import logging
# kafka client
from kafkaClient import init_kafka_producer, get_kafka_producer, LogEntry
import asyncio
import json
from fastapi.security import OAuth2PasswordBearer
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
SERVICE_NAME="loan-notification-websocket"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Properly initialize hash password.
    """
    # init kafka producer
    init_kafka_producer()
    logging.info("Kafka producer retrieved successfully.")
    init_passwordManager()
    logging.info("password for ntoify is set.")
    yield  # This ensures FastAPI correctly waits for app shutdown

app = FastAPI(
    title="Loan Notification API",
    description="real-time notification system using WebSockets, to notify users of loan current status evaluation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# check if boths clients exists
@app.get("/health", summary="Health Check Endpoint", response_model=HealthCheckResponse, tags=["Health"])
def health_check()->HealthCheckResponse:
    """Checks the health of the API and database connection."""
    return HealthCheckResponse(status="healthy")

# WebSocket Manager
class WebSocketManager:
    def __init__(self):
        self.active_connections = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_json_message(self, message: dict, user_id: str):
        """Send a JSON object to the connected WebSocket client."""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))

websocket_manager = WebSocketManager()

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token : str):
    """ WebSocket endpoint that handles JSON communication """
    try:
        user_id = decode_token(credentials=token)
    except:
        await websocket.close(code=4001)  # Unauthorized WebSocket close code
        return
    await websocket_manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()  # Receive raw JSON string
            json_data = json.loads(data)  # Deserialize into a Python dict
            logging.info(f"Received JSON from {user_id}: {json_data}")

            # Example: Send a JSON response back
            response = {"status": "received", "message": "Data received successfully"}
            await websocket_manager.send_json_message(response, user_id)

    except WebSocketDisconnect:
        await websocket_manager.disconnect(user_id)

@app.post("/notify", summary="Notify endpoint used by celeri", status_code=status.HTTP_201_CREATED, response_model=NotifyResponse, tags=["Notify"])
async def notify(authLoanNotificationMessage: AuthLoanNotificationMessage, hashed_password: str = Depends(get_hashed_password), kafkaProducer=Depends(get_kafka_producer))->NotifyResponse:
    error, notifyResponse = None, None
    start_time = get_current_date()
    try:
        # credentials check
        password = authLoanNotificationMessage.password
        if not verify_password(password, hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        # Send message to WebSocket client
        notifyResponse = NotifyResponse(
            loan_id=authLoanNotificationMessage.loan_id, 
            loan_status=authLoanNotificationMessage.loan_status,
            finish=authLoanNotificationMessage.finish,
            message=authLoanNotificationMessage.message
            )
        await websocket_manager.send_json_message(message=notifyResponse.dict(), user_id=authLoanNotificationMessage.user_id)
    
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
            endpoint='notify',
            method='POST', 
            status=status.HTTP_201_CREATED, 
            message='successfully send notification',
            start_time=start_time,
            end_time=end_time,
            metadata={
                'user_id': authLoanNotificationMessage.user_id,
                'load_id': authLoanNotificationMessage.loan_id
            }
            )
        asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
        return notifyResponse
    # error log
    logEntry: LogEntry = LogEntry(
            service=SERVICE_NAME, 
            endpoint='notify',
            method='POST', 
            status=error.status_code, 
            message=error.detail,
            start_time=start_time,
            end_time=end_time,
            metadata={
                'user_id': authLoanNotificationMessage.user_id,
                'load_id': authLoanNotificationMessage.loan_id
            }
            )
    asyncio.create_task(kafkaProducer.send_log_async(logEntry=logEntry))
    raise error
   
 