# 2.3.3 Chi Tiết Theo Domain - Thiết Kế Sản Phẩm DDD

## Tổng Quan Kiến Trúc

Thay vì tách **Book**, **Clothes**, **Generic** thành 3 bảng riêng, hệ thống dùng **một bảng Product duy nhất** với:
- `product_type`: enum định danh loại (Book, Clothes, Generic)
- `attributes`: JSON linh hoạt lưu trữ các thuộc tính riêng biệt

Cách này phù hợp với **DDD (Domain-Driven Design)**: category là dữ liệu (data), không phải service.

---

## 1. Mô Hình Chung (ProductModel)

```python
# product-service/modules/catalog/infrastructure/models/product_model.py

from django.db import models
from django.contrib.postgres.fields import JSONField

class ProductModel(models.Model):
    """
    Bảng sản phẩm thống nhất cho tất cả loại:
    - Book, Clothes, Generic
    """
    PRODUCT_TYPE_CHOICES = [
        ('Book', 'Sách'),
        ('Clothes', 'Quần áo'),
        ('Generic', 'Loại khác'),
    ]
    
    # Thông tin cơ bản
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=500)
    product_type = models.CharField(
        max_length=50,
        choices=PRODUCT_TYPE_CHOICES,
        default='Generic'
    )
    category = models.ForeignKey('Category', on_delete=models.PROTECT)
    brand = models.ForeignKey('Brand', on_delete=models.SET_NULL, null=True)
    
    # Thông tin giá và kho
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    
    # Mô tả
    description = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)
    
    # Attributes linh hoạt: chứa các field riêng theo product_type
    # Ví dụ:
    # Book: {author, isbn, pages, publisher}
    # Clothes: {size, color, material, fit}
    # Generic: {ram, storage, battery, ...}
    attributes = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'catalog_product'
        indexes = [
            models.Index(fields=['product_type', 'category']),
            models.Index(fields=['name', 'price']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_product_type_display()})"
```

---

## 2. Book Domain

### 2.1 Cấu trúc Attributes cho Book

```python
# Book luôn có attributes như sau:
BOOK_ATTRIBUTES_SCHEMA = {
    "author": "str",           # Tác giả
    "isbn": "str",             # ISBN
    "pages": "int",            # Số trang
    "publisher": "str",        # Nhà xuất bản
    "publication_year": "int", # Năm xuất bản
    "language": "str"          # Ngôn ngữ
}
```

### 2.2 Ví Dụ Dữ Liệu Book

```json
{
  "id": 1,
  "name": "Vũ trụ học cơ bản",
  "product_type": "Book",
  "category_id": 5,  // "Sách Khoa học"
  "brand_id": 3,     // "NXB Trẻ"
  "price": 195000.00,
  "stock": 150,
  "description": "Cuốn sách giới thiệu các khái niệm cơ bản về vũ trụ...",
  "image_url": "https://example.com/books/vu-tru-hoc.jpg",
  "attributes": {
    "author": "Carl Sagan",
    "isbn": "978-0-307-40615-9",
    "pages": 408,
    "publisher": "NXB Trẻ",
    "publication_year": 2020,
    "language": "Tiếng Việt"
  }
}
```

### 2.3 Query Book từ Database

```python
# product-service/modules/catalog/infrastructure/querysets/product_queryset.py

class ProductQuerySet(models.QuerySet):
    """
    QuerySet hỗ trợ filter theo loại sản phẩm
    """
    def books(self):
        """Lấy tất cả sách"""
        return self.filter(product_type='Book')
    
    def books_by_author(self, author_name):
        """Lấy sách theo tác giả"""
        return self.filter(
            product_type='Book',
            attributes__author__icontains=author_name
        )
    
    def books_in_stock(self):
        """Lấy sách còn hàng"""
        return self.books().filter(stock__gt=0)
```

### 2.4 Ví Dụ Serializer cho Book

```python
# product-service/modules/catalog/presentation/api/serializers/product_serializer.py

from rest_framework import serializers

class BookSerializer(serializers.Serializer):
    """Serializer cho sách (backward compatible)"""
    id = serializers.IntegerField()
    title = serializers.CharField(source='name')
    author = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField()
    isbn = serializers.SerializerMethodField()
    pages = serializers.SerializerMethodField()
    publisher = serializers.SerializerMethodField()
    
    def get_author(self, obj):
        return obj.attributes.get('author', '')
    
    def get_isbn(self, obj):
        return obj.attributes.get('isbn', '')
    
    def get_pages(self, obj):
        return obj.attributes.get('pages', 0)
    
    def get_publisher(self, obj):
        return obj.attributes.get('publisher', '')
```

---

## 3. Clothes Domain

### 3.1 Cấu trúc Attributes cho Clothes

```python
# Clothes luôn có attributes như sau:
CLOTHES_ATTRIBUTES_SCHEMA = {
    "size": "str",        # S, M, L, XL, XXL
    "color": "str",       # Màu sắc
    "material": "str",    # Chất liệu (Cotton, Polyester, ...)
    "fit": "str",         # Kiểu dáng (Slim, Regular, Loose)
    "care_instruction": "str"  // Hướng dẫn giặt
}
```

### 3.2 Ví Dụ Dữ Liệu Clothes

```json
{
  "id": 101,
  "name": "Áo khoác gió nam",
  "product_type": "Clothes",
  "category_id": 12,  // "Thời trang nam"
  "brand_id": 8,      // "Nike"
  "price": 899000.00,
  "stock": 200,
  "description": "Áo khoác gió chất lượng cao, dáng Slim...",
  "image_url": "https://example.com/clothes/ao-khoac-gio.jpg",
  "attributes": {
    "size": "M",
    "color": "Đen",
    "material": "Polyester 100%",
    "fit": "Slim",
    "care_instruction": "Giặt tay, không nên phơi nắng"
  }
}
```

### 3.3 Query Clothes từ Database

```python
class ProductQuerySet(models.QuerySet):
    def clothes(self):
        """Lấy tất cả quần áo"""
        return self.filter(product_type='Clothes')
    
    def clothes_by_size(self, size):
        """Lấy quần áo theo kích thước"""
        return self.filter(
            product_type='Clothes',
            attributes__size=size
        )
    
    def clothes_by_color(self, color):
        """Lấy quần áo theo màu"""
        return self.filter(
            product_type='Clothes',
            attributes__color__icontains=color
        )
```

### 3.4 Ví Dụ Serializer cho Clothes

```python
class ClothesSerializer(serializers.Serializer):
    """Serializer cho quần áo (backward compatible)"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    brand = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField()
    size = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    material = serializers.SerializerMethodField()
    fit = serializers.SerializerMethodField()
    
    def get_brand(self, obj):
        return obj.brand.name if obj.brand else ''
    
    def get_size(self, obj):
        return obj.attributes.get('size', '')
    
    def get_color(self, obj):
        return obj.attributes.get('color', '')
    
    def get_material(self, obj):
        return obj.attributes.get('material', '')
    
    def get_fit(self, obj):
        return obj.attributes.get('fit', '')
```

---

## 4. Generic Domain (Flexible)

### 4.1 Các Nhóm Generic trong Hệ Thống

```
Generic sản phẩm bao gồm:
- Điện thoại thông minh (ram, storage, battery, camera)
- Máy tính xách tay (cpu, ram, ssd, gpu, screen_size)
- Mỹ phẩm (volume, type, skin_type)
- Nội thất (material, dimensions, weight)
- Máy ảnh (sensor, megapixels, lens_type)
- Đồ chơi (age_group, pieces, material)
- Văn phòng phẩm (paper_type, quantity, color)
- Nhạc cụ (type, strings_count, material)
- Đồ thể thao (sport_type, size, material)
- Thú cưng (pet_type, size, quantity)
- Thực phẩm (weight, expiration_date, origin)
```

### 4.2 Ví Dụ Dữ Liệu Generic - Điện Thoại

```json
{
  "id": 201,
  "name": "iPhone 15 Pro Max 256GB",
  "product_type": "Generic",
  "category_id": 1,  // "Điện thoại thông minh"
  "brand_id": 2,     // "Apple"
  "price": 28999000.00,
  "stock": 50,
  "description": "iPhone 15 Pro Max phiên bản quốc tế...",
  "image_url": "https://example.com/phones/iphone15-pro-max.jpg",
  "attributes": {
    "cpu": "A17 Pro Bionic",
    "ram": "8GB",
    "storage": "256GB",
    "battery": "4685 mAh",
    "camera_main": "48MP",
    "camera_selfie": "12MP",
    "screen_size": "6.7 inch",
    "color": "Titanium Black"
  }
}
```

### 4.3 Ví Dụ Dữ Liệu Generic - Mỹ Phẩm

```json
{
  "id": 202,
  "name": "L'Oréal Paris Revitalift Eye Cream",
  "product_type": "Generic",
  "category_id": 8,  // "Mỹ phẩm"
  "brand_id": 5,     // "L'Oréal"
  "price": 450000.00,
  "stock": 300,
  "description": "Kem dưỡng vùng mắt chống lão hóa...",
  "image_url": "https://example.com/beauty/loreal-eye-cream.jpg",
  "attributes": {
    "volume": "15ml",
    "type": "Eye Cream",
    "skin_type": "All skin types",
    "benefit": "Anti-aging, Hydrating",
    "origin": "France",
    "expiration_date": "2025-12-31"
  }
}
```

### 4.4 Query Generic từ Database

```python
class ProductQuerySet(models.QuerySet):
    def generic(self):
        """Lấy tất cả sản phẩm loại Generic"""
        return self.filter(product_type='Generic')
    
    def electronics_in_stock(self):
        """Lấy điện tử còn hàng"""
        return self.filter(
            product_type='Generic',
            category__name='Điện thoại thông minh',
            stock__gt=0
        )
    
    def beauty_by_skin_type(self, skin_type):
        """Lấy mỹ phẩm theo loại da"""
        return self.filter(
            product_type='Generic',
            category__name='Mỹ phẩm',
            attributes__skin_type__icontains=skin_type
        )
```

---

## 5. Unified API Endpoint

### 5.1 GET /api/products/ - Lấy tất cả sản phẩm

```python
# product-service/modules/catalog/presentation/api/views/product_view.py

from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

class ProductViewSet(ViewSet):
    def list(self, request):
        """
        Lấy danh sách tất cả sản phẩm
        Query params:
        - product_type: Book | Clothes | Generic
        - category_id: int
        - price_min / price_max: float
        - search: str (tìm trong name, author, material, ...)
        """
        queryset = ProductModel.objects.all()
        
        # Filter by product_type
        product_type = request.query_params.get('product_type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        # Filter by category
        category_id = request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by price range
        price_min = request.query_params.get('price_min')
        price_max = request.query_params.get('price_max')
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)
        
        # Search
        search = request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(attributes__author__icontains=search) |
                Q(attributes__color__icontains=search)
            )
        
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def books(self, request):
        """GET /api/products/books/ - Lấy tất cả sách"""
        queryset = ProductModel.objects.filter(product_type='Book')
        serializer = BookSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def clothes(self, request):
        """GET /api/products/clothes/ - Lấy tất cả quần áo"""
        queryset = ProductModel.objects.filter(product_type='Clothes')
        serializer = ClothesSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def generic(self, request):
        """GET /api/products/generic/ - Lấy tất cả loại khác"""
        queryset = ProductModel.objects.filter(product_type='Generic')
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)
```

---

## 6. Thống Kê - 17 Category & 380 Sản Phẩm

### 6.1 Phân Bố Sản Phẩm Theo Loại

| Loại | Số lượng | Ví dụ Category |
|------|---------|---|
| Book | 40 | Sách Khoa học, Sách Kỹ năng, Sách Tâm lý |
| Clothes | 40 | Thời trang nam, Thời trang nữ, Giày dép |
| Generic | 300 | Điện thoại, Laptop, Mỹ phẩm, Nội thất, ... |
| **TỔNG** | **380** | **17 danh mục** |

### 6.2 Ví Dụ 17 Category

1. **Sách Khoa học** (Book) → 20 sản phẩm
2. **Sách Kỹ năng** (Book) → 20 sản phẩm
3. **Thời trang nam** (Clothes) → 20 sản phẩm
4. **Thời trang nữ** (Clothes) → 20 sản phẩm
5. **Điện thoại thông minh** (Generic) → 40 sản phẩm
6. **Máy tính xách tay** (Generic) → 40 sản phẩm
7. **Mỹ phẩm** (Generic) → 40 sản phẩm
8. **Nội thất** (Generic) → 30 sản phẩm
9. **Máy ảnh** (Generic) → 30 sản phẩm
10. **Đồ chơi** (Generic) → 20 sản phẩm
11. **Văn phòng phẩm** (Generic) → 20 sản phẩm
12. **Nhạc cụ** (Generic) → 20 sản phẩm
13. **Đồ thể thao** (Generic) → 20 sản phẩm
14. **Thú cưng** (Generic) → 20 sản phẩm
15. **Thực phẩm** (Generic) → 20 sản phẩm
16. **Giày dép** (Generic) → 19 sản phẩm
17. **Phụ kiện** (Generic) → 11 sản phẩm

---

## 7. Kết Luận

**Lợi ích của thiết kế này:**

✅ **Linh hoạt**: Thêm loại sản phẩm mới không cần migration DB, chỉ cần thêm giá trị `product_type` và schema mới.

✅ **DDD**: Category là data, không phải service, giúp mô hình rõ ràng theo miền kinh doanh.

✅ **Backward compatible**: Có thể query theo loại (Book, Clothes, Generic) mà không thay đổi schema.

✅ **Scalable**: JSON attributes cho phép lưu bất kỳ metadata nào mà không cần alter table.

✅ **Thống nhất**: Một endpoint `/api/products/` xử lý tất cả loại thay vì 3 endpoint riêng.
