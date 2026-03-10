from django.contrib import admin
from .models import Customer, AgentConversation, AgentMessage

admin.site.register(Customer)
admin.site.register(AgentConversation)
admin.site.register(AgentMessage)
