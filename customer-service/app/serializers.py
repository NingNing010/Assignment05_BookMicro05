from rest_framework import serializers
from .models import Customer, AgentConversation, AgentMessage


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class AgentMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentMessage
        fields = ['id', 'role', 'content', 'intent', 'created_at']


class AgentConversationSerializer(serializers.ModelSerializer):
    messages = AgentMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AgentConversation
        fields = ['id', 'customer', 'created_at', 'messages']


class AgentChatInputSerializer(serializers.Serializer):
    """Validates incoming chat requests."""
    customer_id = serializers.IntegerField()
    message = serializers.CharField(max_length=1000)
    conversation_id = serializers.IntegerField(required=False)
