from django.contrib import admin
from .models import Book, Category, Publisher


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'address']
    search_fields = ['name', 'email']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description']
    search_fields = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'price', 'stock', 'category', 'publisher']
    list_filter = ['category', 'publisher']
    search_fields = ['title', 'author', 'isbn']
    list_editable = ['price', 'stock']
