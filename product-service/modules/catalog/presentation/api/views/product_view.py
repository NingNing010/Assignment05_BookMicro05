"""
Product views — REST API for Product CRUD.

Provides:
- /products/         — unified product list/create
- /books/            — backward-compatible book endpoints (filter by product_type=Book)
- /clothes/          — backward-compatible clothes endpoints (filter by product_type=Clothes)
- /publishers/       — backward-compatible publisher endpoints (mapped to Brand)
- /brands/           — brand list/create
- /product-types/    — product type list/create
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.brand_model import BrandModel
from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel
from modules.catalog.infrastructure.models.variant_model import VariantModel
from modules.catalog.presentation.api.serializers.product_serializer import (
    ProductSerializer,
    BookCompatSerializer,
    ClothesCompatSerializer,
    BrandSerializer,
    ProductTypeSerializer,
    VariantSerializer,
)


# ──────────────────────────────────────────────
# Unified Product CRUD
# ──────────────────────────────────────────────

class ProductListCreate(APIView):
    def get(self, request):
        qs = ProductModel.objects.select_related('product_type', 'category', 'brand').all()
        product_type = request.GET.get('type')
        if product_type:
            qs = qs.filter(product_type__name__iexact=product_type)
        return Response(ProductSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetail(APIView):
    def get_object(self, pk):
        try:
            return ProductModel.objects.select_related(
                'product_type', 'category', 'brand',
            ).get(pk=pk)
        except ProductModel.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': f'Product #{pk} deleted.'}, status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Backward-Compatible Book CRUD (/books/)
# ──────────────────────────────────────────────

class BookListCreate(APIView):
    """Mimics the old book-service /books/ endpoint."""

    def get(self, request):
        qs = ProductModel.objects.select_related(
            'product_type', 'category', 'brand',
        ).filter(product_type__name='Book')
        return Response(BookCompatSerializer(qs, many=True).data)

    def post(self, request):
        serializer = BookCompatSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetail(APIView):
    def get_object(self, pk):
        try:
            return ProductModel.objects.select_related(
                'product_type', 'category', 'brand',
            ).get(pk=pk, product_type__name='Book')
        except ProductModel.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(BookCompatSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookCompatSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookCompatSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Book not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': f'Book #{pk} deleted.'}, status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Backward-Compatible Clothes CRUD (/clothes/)
# ──────────────────────────────────────────────

class ClothesListCreate(APIView):
    """Mimics the old clothes-service /clothes/ endpoint."""

    def get(self, request):
        qs = ProductModel.objects.select_related(
            'product_type', 'category', 'brand',
        ).filter(product_type__name='Clothes')
        return Response(ClothesCompatSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ClothesCompatSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClothesDetail(APIView):
    def get_object(self, pk):
        try:
            return ProductModel.objects.select_related(
                'product_type', 'category', 'brand',
            ).get(pk=pk, product_type__name='Clothes')
        except ProductModel.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Clothes not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ClothesCompatSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Clothes not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClothesCompatSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Clothes not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClothesCompatSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Clothes not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': f'Clothes #{pk} deleted.'}, status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Backward-Compatible Publisher CRUD (/publishers/) → Brand
# ──────────────────────────────────────────────

class PublisherListCreate(APIView):
    """Maps old /publishers/ to Brand model."""

    def get(self, request):
        brands = BrandModel.objects.all()
        return Response(BrandSerializer(brands, many=True).data)

    def post(self, request):
        serializer = BrandSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublisherDetail(APIView):
    def get_object(self, pk):
        try:
            return BrandModel.objects.get(pk=pk)
        except BrandModel.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Publisher not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(BrandSerializer(obj).data)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Publisher not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BrandSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Publisher not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BrandSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Publisher not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': f'Publisher #{pk} deleted.'}, status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# Brand CRUD (/brands/)
# ──────────────────────────────────────────────

class BrandListCreate(APIView):
    def get(self, request):
        return Response(BrandSerializer(BrandModel.objects.all(), many=True).data)

    def post(self, request):
        serializer = BrandSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# ProductType CRUD (/product-types/)
# ──────────────────────────────────────────────

class ProductTypeListCreate(APIView):
    def get(self, request):
        return Response(ProductTypeSerializer(ProductTypeModel.objects.all(), many=True).data)

    def post(self, request):
        serializer = ProductTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Variant endpoints
# ──────────────────────────────────────────────

class VariantListCreate(APIView):
    def get(self, request):
        product_id = request.GET.get('product_id')
        qs = VariantModel.objects.select_related('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return Response(VariantSerializer(qs, many=True).data)

    def post(self, request):
        serializer = VariantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────

class HealthLiveView(APIView):
    def get(self, request):
        return Response({'status': 'live', 'service': 'product-service'})


class HealthReadyView(APIView):
    def get(self, request):
        ProductModel.objects.count()
        return Response({'status': 'ready', 'service': 'product-service'})
