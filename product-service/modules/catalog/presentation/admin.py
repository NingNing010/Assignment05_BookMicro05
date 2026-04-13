"""
Django Admin configuration for Catalog models.
"""
from django.contrib import admin
from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.brand_model import BrandModel
from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel
from modules.catalog.infrastructure.models.variant_model import VariantModel


@admin.register(ProductTypeModel)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description']
    search_fields = ['name']


@admin.register(BrandModel)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'address']
    search_fields = ['name', 'email']


@admin.register(CategoryModel)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'parent', 'description']
    search_fields = ['name']
    list_filter = ['parent']


@admin.register(ProductModel)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'product_type', 'price', 'stock', 'category', 'brand']
    list_filter = ['product_type', 'category', 'brand']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock']


@admin.register(VariantModel)
class VariantAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'sku', 'size', 'color', 'stock', 'price_override']
    list_filter = ['product']
    search_fields = ['sku', 'size', 'color']
