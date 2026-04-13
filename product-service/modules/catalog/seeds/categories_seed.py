"""
Seed script: Categories
Run: python manage.py shell < modules/catalog/seeds/categories_seed.py
"""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from modules.catalog.infrastructure.models.category_model import CategoryModel

CATEGORIES = [
    {'name': 'Programming', 'description': 'Books about software development and programming languages'},
    {'name': 'Data Science', 'description': 'Books about data analysis, ML, and AI'},
    {'name': 'Architecture', 'description': 'Books about software architecture and system design'},
    {'name': 'DevOps', 'description': 'Books about deployment, CI/CD, and infrastructure'},
    {'name': 'Cooking', 'description': 'Books and products related to cooking and cuisine'},
    {'name': 'Lifestyle', 'description': 'Products for a better lifestyle'},
    {'name': 'Household', 'description': 'Household products and guides'},
    {'name': 'Business', 'description': 'Books about business, finance, and marketing'},
    {'name': 'Children', 'description': 'Products for children'},
    {'name': 'Fashion', 'description': 'Clothing and fashion products'},
    {'name': 'Sportswear', 'description': 'Athletic and sports clothing'},
]

for cat_data in CATEGORIES:
    obj, created = CategoryModel.objects.get_or_create(
        name=cat_data['name'],
        defaults={'description': cat_data['description']},
    )
    status = 'CREATED' if created else 'EXISTS'
    print(f'  [{status}] Category: {obj.name}')

print(f'\nTotal categories: {CategoryModel.objects.count()}')
