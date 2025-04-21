import os
import logging
from pymongo import MongoClient
from django.conf import settings

# Configure logger
logger = logging.getLogger(__name__)

def get_database():
    """
    Get a connection to the MongoDB database
    
    Returns:
        MongoDB database object
    """
    try:
        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB_NAME]
        logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
        return db
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {str(e)}")
        raise

def get_collection(collection_name):
    """
    Get a MongoDB collection from the database
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        MongoDB collection object
    """
    db = get_database()
    return db[collection_name]