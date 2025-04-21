from django.db import models
from django.conf import settings

# Access MongoDB collections
ai_training_data_collection = settings.MONGODB_DB['ai_training_data']
transcription_records_collection = settings.MONGODB_DB['transcription_records']
ai_task_predictions_collection = settings.MONGODB_DB['ai_task_predictions']
