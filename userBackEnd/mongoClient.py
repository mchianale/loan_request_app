from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.synchronous.database import Database
from dotenv import load_dotenv
import os
load_dotenv()

# Global client instance
# Synchronous client (for sync operations)
sync_client: MongoClient = None
# Asynchronous client (for async operations)
async_client: AsyncIOMotorClient = None

async def init_client()->None:
    """
    Initialize MongoDB client asynchronously.
    """
    global sync_client, async_client
    # sync one 
    if sync_client is None:
        try:
            user = os.getenv("MONGO_INITDB_ROOT_USERNAME")
            password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
            sync_client = MongoClient(f"mongodb://{user}:{password}@mongodb:27017")
        except Exception as e:
            raise Exception(f"Failed to connect to Sync MongoDB: {e}")

    # async client 
    if async_client is None:
        try:
            user = os.getenv("MONGO_INITDB_ROOT_USERNAME")
            password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
            async_client = AsyncIOMotorClient(f'mongodb://{user}:{password}@mongodb:27017')
        except Exception as e:
            raise Exception(f"Failed to connect to MongoDB: {e}")

def get_async_db_handle()->AsyncIOMotorDatabase:
    """
    Return the initialized MongoDB client.
    """
    if async_client is None:
        raise Exception("Database client is not initialized. Ensure `init_client()` is called at startup.")
    return async_client[os.getenv("DATABASE_NAME")]

def get_sync_db_handle()->Database:
    """
    Return the initialized MongoDB client.
    """
    if sync_client is None:
        raise Exception("Database client is not initialized. Ensure `init_client()` is called at startup.")
    return sync_client[os.getenv("DATABASE_NAME")]
