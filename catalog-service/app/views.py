from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Category
from .serializers import CategorySerializer
import requests

BOOK_SERVICE_URL = "http://book-service:8000"


class CategoryListCreate(APIView):
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetail(APIView):
    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(CategorySerializer(category).data)

    def put(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        category.delete()
        return Response({"message": f"Category #{pk} deleted."}, status=status.HTTP_204_NO_CONTENT)


class CatalogBooks(APIView):
    """View books from book-service through catalog"""

    def get(self, request):
        r = requests.get(f"{BOOK_SERVICE_URL}/books/")
        return Response(r.json())
