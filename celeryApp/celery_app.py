from celery import Celery
from dotenv import load_dotenv
import os
load_dotenv()

# Celery configuration
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
REDIS_CELERY_DB_INDEX = os.environ.get('REDIS_CELERY_DB_INDEX')

RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST')
RABBITMQ_USERNAME = os.environ.get('RABBITMQ_USERNAME')
RABBITMQ_PASSWORD = os.environ.get('RABBITMQ_PASSWORD')
RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT')

BROKER_CONN_URI = f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}"
BACKEND_CONN_URI = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB_INDEX}"
BACKEND_CONN_URI = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_CELERY_DB_INDEX}"

LOAN_TOPIC = os.environ.get('LOAN_TOPIC')
CREDIT_CHECK_URL = os.environ.get('CREDIT_CHECK_URL')
PROPERTY_CHECK_URL = os.environ.get('PROPERTY_CHECK_URL')
DECISION_URL = os.environ.get('DECISION_URL')
NOTIFICATION_URL = os.environ.get('NOTIFICATION_URL')
UPDATE_LOAN_URL = os.environ.get('UPDATE_LOAN_URL')
# password to notify
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
# Initialize Celery worker
app = Celery(
    "laon_service",
    broker_connection_retry_on_startup=True,  # Fix for future Celery 6
    broker_pool_limit=None,
    broker_connection_max_retries=5,
    broker=BROKER_CONN_URI,  # Secure RabbitMQ connection
    backend=BACKEND_CONN_URI,  # Secure Redis connection   
    include=["tasks"]
)