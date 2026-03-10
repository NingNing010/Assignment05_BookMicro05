from django.urls import path
from .views import (
    CustomerListCreate,
    CustomerDetail,
    AgentChatView,
    AgentConversationListView,
    AgentConversationDetailView,
    AgentHelpView,
)

urlpatterns = [
    path('customers/', CustomerListCreate.as_view()),
    path('customers/<int:pk>/', CustomerDetail.as_view()),

    # AI Agent endpoints
    path('agent/chat/', AgentChatView.as_view()),
    path('agent/conversations/', AgentConversationListView.as_view()),
    path('agent/conversations/<int:pk>/', AgentConversationDetailView.as_view()),
    path('agent/help/', AgentHelpView.as_view()),
]
