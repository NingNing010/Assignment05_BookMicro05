from django.urls import path
from .views import RecommendationForCustomer, RecommendationList, PredictiveAIBiLSTM, GraphRAGChat, UserTracking

urlpatterns = [
    path('recommendations/', RecommendationList.as_view()),
    path('recommendations/<int:customer_id>/', RecommendationForCustomer.as_view()),
    path('ai/predict/', PredictiveAIBiLSTM.as_view()),
    path('ai/chat/', GraphRAGChat.as_view()),
    path('ai/track/', UserTracking.as_view()),
]
