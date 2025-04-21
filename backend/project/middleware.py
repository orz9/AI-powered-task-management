import logging
from django.conf import settings
from django.http import HttpResponse
import pymongo
import json

logger = logging.getLogger(__name__)

class MongoDBConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check MongoDB connection before processing request
        if hasattr(settings, 'MONGODB_DB') and settings.MONGODB_CLIENT:
            try:
                # Check if MongoDB is still connected
                settings.MONGODB_CLIENT.admin.command('ping')
            except pymongo.errors.ConnectionFailure:
                logger.error("MongoDB connection lost")
                # For API requests, return JSON error
                if request.path.startswith('/api/'):
                    return HttpResponse(
                        json.dumps({"error": "Database connection unavailable"}),
                        content_type="application/json",
                        status=503
                    )
                # For other requests, let them proceed (they might not need MongoDB)
        
        response = self.get_response(request)
        return response