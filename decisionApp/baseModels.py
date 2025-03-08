from pydantic import BaseModel, Field
# health
class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="The current status of the API (e.g., healthy, degraded)")
    