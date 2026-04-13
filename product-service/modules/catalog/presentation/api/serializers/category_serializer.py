"""
Category serializer.
"""
from rest_framework import serializers
from modules.catalog.infrastructure.models.category_model import CategoryModel


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = '__all__'
