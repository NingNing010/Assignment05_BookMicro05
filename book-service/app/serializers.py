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

    def validate_stock(self, value):
        if value is None:
            return value
        if not isinstance(value, int):
            raise serializers.ValidationError("Stock must be an integer")
        if value < 0:
            raise serializers.ValidationError("Stock must be >= 0")
        return value

    def validate_price(self, value):
        if value is None:
            return value
        if value <= 0:
            raise serializers.ValidationError("Price must be > 0")
        return value
