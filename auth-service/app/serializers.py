from rest_framework import serializers
from .models import UserAccount


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ['id', 'email', 'password', 'full_name', 'role', 'created_at']
        extra_kwargs = {'password': {'write_only': True}}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ['id', 'email', 'full_name', 'role', 'is_active', 'created_at']
