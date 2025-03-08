from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone, timedelta

import uuid

class LogEntry(BaseModel):
    log_id: str = Field(
        default=str(uuid.uuid4()),
        description="A unique identifier for the log entry."
    )
    log_timestamp: datetime = Field(
        default=datetime.now(timezone(timedelta(hours=1))), 
        description="Creation date of the log."
    )
    service: str = Field(
        ..., 
        description="The name of the service generating the log (e.g., 'loan-service', 'auth-service')."
    )
    endpoint: str = Field(
        ...,
        description="Called endpoint."
    )
    method: str = Field(
        ..., 
        description="The HTTP method used for the request (e.g., 'GET', 'POST', 'PUT', 'DELETE')."
    )
    status: int = Field(
        default=200, 
        description="The HTTP response status code (e.g., 200 for success, 400 for bad request)."
    )
    message: str = Field(
        default=None, 
        description="A human-readable message describing the log event."
    )
    start_time: datetime = Field(
        ..., 
        description="The timestamp when the request or process started."
    )
    end_time: datetime = Field(
        ..., 
        description="The timestamp when the request or process ended."
    )
    duration_ms: float = Field(
        default=None,
        description="The total execution time in milliseconds, calculated as (end_time - start_time)."
    )
    metadata: dict = Field(
        default=None, 
        description="Additional metadata related to the request, such as user_id, loan_id, or request details."
    )

    @model_validator(mode="after")  # Runs automatically after validation
    def compute_duration(cls, values)->float:
        values.duration_ms = (values.end_time - values.start_time).total_seconds() * 1000
        return values

