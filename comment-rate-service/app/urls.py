from django.urls import path
from .views import (
    ReviewListCreate,
    ReviewDetail,
    BookReviews,
    BehaviorModelTrain,
    BehaviorCustomerAnalyze,
    KnowledgeBaseList,
    KnowledgeBaseRebuild,
    RAGBehaviorChat,
)

urlpatterns = [
    path('reviews/', ReviewListCreate.as_view()),
    path('reviews/<int:pk>/', ReviewDetail.as_view()),
    path('reviews/book/<int:book_id>/', BookReviews.as_view()),
    path('behavior/train/', BehaviorModelTrain.as_view()),
    path('behavior/customer/<int:customer_id>/', BehaviorCustomerAnalyze.as_view()),
    path('kb/', KnowledgeBaseList.as_view()),
    path('kb/rebuild/', KnowledgeBaseRebuild.as_view()),
    path('rag/chat/', RAGBehaviorChat.as_view()),
    # Aliases to support api-gateway /api/proxy/reviews/<path>
    path('reviews/behavior/train/', BehaviorModelTrain.as_view()),
    path('reviews/behavior/customer/<int:customer_id>/', BehaviorCustomerAnalyze.as_view()),
    path('reviews/kb/', KnowledgeBaseList.as_view()),
    path('reviews/kb/rebuild/', KnowledgeBaseRebuild.as_view()),
    path('reviews/rag/chat/', RAGBehaviorChat.as_view()),
]
