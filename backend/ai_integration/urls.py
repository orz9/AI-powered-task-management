from django.urls import path
from . import views

urlpatterns = [
    path('process-audio/', views.ProcessAudioView.as_view(), name='process-audio'),
    path('predict-tasks/', views.PredictTasksView.as_view(), name='predict-tasks'),
    path('analyze-tasks/<str:person_id>/', views.AnalyzeTasksView.as_view(), name='analyze-tasks'),
    path('save-tasks/', views.SaveExtractedTasksView.as_view(), name='save-tasks'),
]
