"""
Category views — REST API for Category CRUD.
Also serves the old catalog-service /catalog/books/ proxy endpoint.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.presentation.api.serializers.category_serializer import CategorySerializer
from modules.catalog.presentation.api.serializers.product_serializer import BookCompatSerializer


class CategoryListCreate(APIView):
    def get(self, request):
        categories = CategoryModel.objects.all()
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetail(APIView):
    def get_object(self, pk):
        try:
            return CategoryModel.objects.get(pk=pk)
        except CategoryModel.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CategorySerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': f'Category #{pk} deleted.'}, status=status.HTTP_204_NO_CONTENT)


class CatalogBooks(APIView):
    """Backward-compatible endpoint for old catalog-service /catalog/books/."""
    def get(self, request):
        qs = ProductModel.objects.select_related(
            'product_type', 'category', 'brand',
        ).filter(product_type__name='Book')
        return Response(BookCompatSerializer(qs, many=True).data)
