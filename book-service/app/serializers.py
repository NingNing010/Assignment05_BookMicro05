from rest_framework import serializers
from .models import Book, Category, Publisher


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class BookSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True)

    class Meta:
        model = Book
        fields = '__all__'
