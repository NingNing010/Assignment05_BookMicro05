"""
Product serializers — DRF serializers for the Product API.
Provides backward-compatible output for /books/ and /clothes/ endpoints.
"""
from rest_framework import serializers
from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.variant_model import VariantModel
from modules.catalog.infrastructure.models.brand_model import BrandModel
from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandModel
        fields = '__all__'


class ProductTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTypeModel
        fields = '__all__'


class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantModel
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    """Full product serializer used for /products/ endpoint."""
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    brand_name = serializers.CharField(source='brand.name', read_only=True, default='')
    product_type_name = serializers.CharField(source='product_type.name', read_only=True, default='')
    variants = VariantSerializer(many=True, read_only=True)

    class Meta:
        model = ProductModel
        fields = '__all__'

    def validate_stock(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('Stock must be >= 0')
        return value

    def validate_price(self, value):
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError('Price must be > 0')
            if value != int(value):
                raise serializers.ValidationError('Price must be a whole VND amount')
        return value


class BookCompatSerializer(serializers.ModelSerializer):
    """
    Backward-compatible serializer mimicking the old BookSerializer output.
    Maps: name→title, brand→publisher, attributes.author→author, attributes.isbn→isbn
    """
    title = serializers.CharField(source='name')
    author = serializers.SerializerMethodField()
    isbn = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    publisher = serializers.IntegerField(source='brand_id', required=False, allow_null=True)
    publisher_name = serializers.CharField(source='brand.name', read_only=True, default='')

    class Meta:
        model = ProductModel
        fields = [
            'id', 'title', 'author', 'image_url', 'price', 'stock',
            'description', 'isbn', 'category', 'category_name',
            'publisher', 'publisher_name',
        ]

    def get_author(self, obj):
        return (obj.attributes or {}).get('author', '')

    def get_isbn(self, obj):
        return (obj.attributes or {}).get('isbn', '')

    def validate_stock(self, value):
        if value is not None:
            if not isinstance(value, int):
                raise serializers.ValidationError('Stock must be an integer')
            if value < 0:
                raise serializers.ValidationError('Stock must be >= 0')
        return value

    def validate_price(self, value):
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError('Price must be > 0')
            if value != int(value):
                raise serializers.ValidationError('Price must be a whole VND amount')
        return value

    def to_internal_value(self, data):
        """Convert incoming book-format data to Product format."""
        internal = {}
        if 'title' in data:
            internal['name'] = data['title']
        if 'price' in data:
            internal['price'] = data['price']
        if 'stock' in data:
            internal['stock'] = data['stock']
        if 'description' in data:
            internal['description'] = data['description']
        if 'image_url' in data:
            internal['image_url'] = data['image_url']
        if 'category' in data:
            internal['category'] = data['category']
        if 'publisher' in data:
            internal['brand_id'] = data['publisher']

        # Merge author/isbn into attributes
        attrs = {}
        if 'author' in data:
            attrs['author'] = data['author']
        if 'isbn' in data:
            attrs['isbn'] = data['isbn']
        if attrs:
            internal['attributes'] = attrs

        return internal

    def create(self, validated_data):
        from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel
        book_type, _ = ProductTypeModel.objects.get_or_create(name='Book')
        attrs = validated_data.pop('attributes', {})
        obj = ProductModel.objects.create(
            product_type=book_type,
            attributes=attrs,
            **validated_data,
        )
        return obj

    def update(self, instance, validated_data):
        attrs = validated_data.pop('attributes', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if attrs:
            current_attrs = instance.attributes or {}
            current_attrs.update(attrs)
            instance.attributes = current_attrs
        instance.save()
        return instance


class ClothesCompatSerializer(serializers.ModelSerializer):
    """
    Backward-compatible serializer mimicking the old ClothesSerializer output.
    Maps: attributes.size→size, attributes.color→color, brand→brand field
    """
    brand = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()

    class Meta:
        model = ProductModel
        fields = [
            'id', 'name', 'brand', 'size', 'color',
            'image_url', 'price', 'stock', 'description',
        ]

    def get_brand(self, obj):
        return (obj.attributes or {}).get('brand', obj.brand.name if obj.brand else '')

    def get_size(self, obj):
        return (obj.attributes or {}).get('size', '')

    def get_color(self, obj):
        return (obj.attributes or {}).get('color', '')

    def to_internal_value(self, data):
        internal = {}
        if 'name' in data:
            internal['name'] = data['name']
        if 'price' in data:
            internal['price'] = data['price']
        if 'stock' in data:
            internal['stock'] = data['stock']
        if 'description' in data:
            internal['description'] = data['description']
        if 'image_url' in data:
            internal['image_url'] = data['image_url']

        attrs = {}
        if 'brand' in data:
            attrs['brand'] = data['brand']
        if 'size' in data:
            attrs['size'] = data['size']
        if 'color' in data:
            attrs['color'] = data['color']
        if attrs:
            internal['attributes'] = attrs

        return internal

    def create(self, validated_data):
        from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel
        clothes_type, _ = ProductTypeModel.objects.get_or_create(name='Clothes')
        attrs = validated_data.pop('attributes', {})
        obj = ProductModel.objects.create(
            product_type=clothes_type,
            attributes=attrs,
            **validated_data,
        )
        return obj

    def update(self, instance, validated_data):
        attrs = validated_data.pop('attributes', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if attrs:
            current_attrs = instance.attributes or {}
            current_attrs.update(attrs)
            instance.attributes = current_attrs
        instance.save()
        return instance
