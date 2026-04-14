"""
Seed script: Products (Books + Clothes)
Run: python manage.py shell < modules/catalog/seeds/products_seed.py
"""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel


def vnd_price(value):
    return int(round(float(value) * 1000 / 1000) * 1000)
from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.brand_model import BrandModel

# ── Product Types ──────────────────────────────
book_type, _ = ProductTypeModel.objects.get_or_create(name='Book', defaults={'description': 'Physical or digital books'})
clothes_type, _ = ProductTypeModel.objects.get_or_create(name='Clothes', defaults={'description': 'Clothing and apparel'})
print(f'Product Types ready: {list(ProductTypeModel.objects.values_list("name", flat=True))}')

# ── Brands (from old Publishers + Clothes brands) ──
brands_data = [
    {'name': 'O\'Reilly Media', 'email': 'info@oreilly.com', 'address': 'Sebastopol, CA'},
    {'name': 'Pearson', 'email': 'info@pearson.com', 'address': 'London, UK'},
    {'name': 'Manning', 'email': 'info@manning.com', 'address': 'Shelter Island, NY'},
    {'name': 'Nike', 'description': 'Athletic apparel and footwear'},
    {'name': 'Adidas', 'description': 'Sportswear and accessories'},
    {'name': 'Uniqlo', 'description': 'Casual wear'},
    {'name': 'Zara', 'description': 'Fast fashion'},
    {'name': 'H&M', 'description': 'Affordable fashion'},
]
brand_map = {}
for bd in brands_data:
    obj, created = BrandModel.objects.get_or_create(name=bd['name'], defaults=bd)
    brand_map[bd['name']] = obj
    print(f'  {"CREATED" if created else "EXISTS"} Brand: {obj.name}')

# ── Helper to find category ────────────────────
def get_cat(name):
    try:
        return CategoryModel.objects.get(name=name)
    except CategoryModel.DoesNotExist:
        return None

# ── Books (migrated from old bookstore_book data) ──
books = [
    {'name': 'Clean Code', 'price': vnd_price(39.99), 'stock': 15, 'category': 'Programming', 'brand': 'Pearson',
     'description': 'A Handbook of Agile Software Craftsmanship by Robert C. Martin',
     'image_url': 'https://m.media-amazon.com/images/I/41xShlnTZTL._SX376_BO1,204,203,200_.jpg',
     'attributes': {'author': 'Robert C. Martin', 'isbn': '978-0-13-235088-4'}},
    {'name': 'Design Patterns', 'price': vnd_price(49.99), 'stock': 10, 'category': 'Architecture', 'brand': 'Pearson',
     'description': 'Elements of Reusable Object-Oriented Software',
     'image_url': 'https://m.media-amazon.com/images/I/51szD9HC9pL._SX395_BO1,204,203,200_.jpg',
     'attributes': {'author': 'Gang of Four', 'isbn': '978-0-201-63361-0'}},
    {'name': 'Python Crash Course', 'price': vnd_price(35.99), 'stock': 20, 'category': 'Programming', 'brand': 'Pearson',
     'description': 'A Hands-On, Project-Based Introduction to Programming',
     'image_url': 'https://m.media-amazon.com/images/I/51W1sBHFP1L._SX376_BO1,204,203,200_.jpg',
     'attributes': {'author': 'Eric Matthes', 'isbn': '978-1-59327-928-8'}},
    {'name': 'Hands-On Machine Learning', 'price': vnd_price(59.99), 'stock': 8, 'category': 'Data Science', 'brand': "O'Reilly Media",
     'description': 'Concepts, Tools, and Techniques to Build Intelligent Systems',
     'image_url': 'https://m.media-amazon.com/images/I/51aqYc1QyrL._SX379_BO1,204,203,200_.jpg',
     'attributes': {'author': 'Aurélien Géron', 'isbn': '978-1-492-03264-9'}},
    {'name': 'The Pragmatic Programmer', 'price': vnd_price(44.99), 'stock': 12, 'category': 'Programming', 'brand': 'Pearson',
     'description': 'Your Journey to Mastery',
     'image_url': 'https://m.media-amazon.com/images/I/51cUVaBWZzL._SX380_BO1,204,203,200_.jpg',
     'attributes': {'author': 'David Thomas, Andrew Hunt', 'isbn': '978-0-13-595705-9'}},
    {'name': 'Docker Deep Dive', 'price': vnd_price(29.99), 'stock': 18, 'category': 'DevOps', 'brand': 'Manning',
     'description': 'Zero to Docker in a single book',
     'image_url': 'https://m.media-amazon.com/images/I/51E2055UFAL._SX331_BO1,204,203,200_.jpg',
     'attributes': {'author': 'Nigel Poulton', 'isbn': '978-1-521-82280-0'}},
    {'name': 'Building Microservices', 'price': vnd_price(45.99), 'stock': 14, 'category': 'Architecture', 'brand': "O'Reilly Media",
     'description': 'Designing Fine-Grained Systems',
     'image_url': 'https://m.media-amazon.com/images/I/51bSBaXrekL._SX379_BO1,204,203,200_.jpg',
     'attributes': {'author': 'Sam Newman', 'isbn': '978-1-492-03402-5'}},
    {'name': 'JavaScript: The Good Parts', 'price': vnd_price(25.99), 'stock': 22, 'category': 'Programming', 'brand': "O'Reilly Media",
     'description': 'Unearthing the Excellence in JavaScript',
     'image_url': 'https://m.media-amazon.com/images/I/5131OWtQRaL._SX381_BO1,204,203,200_.jpg',
     'attributes': {'author': 'Douglas Crockford', 'isbn': '978-0-596-51774-8'}},
    {'name': 'Kubernetes in Action', 'price': vnd_price(49.99), 'stock': 9, 'category': 'DevOps', 'brand': 'Manning',
     'description': 'Deep dive into Kubernetes orchestration',
     'image_url': 'https://m.media-amazon.com/images/I/51GjNdhC5EL._SX397_BO1,204,203,200_.jpg',
     'attributes': {'author': 'Marko Lukša', 'isbn': '978-1-617-29372-6'}},
    {'name': 'Deep Learning with Python', 'price': vnd_price(54.99), 'stock': 11, 'category': 'Data Science', 'brand': 'Manning',
     'description': 'An introduction to deep learning with Keras',
     'image_url': 'https://m.media-amazon.com/images/I/51h5d4dYaoL._SX258_BO1,204,203,200_.jpg',
     'attributes': {'author': 'François Chollet', 'isbn': '978-1-617-29643-7'}},
    {'name': 'Domain-Driven Design', 'price': vnd_price(55.99), 'stock': 7, 'category': 'Architecture', 'brand': 'Pearson',
     'description': 'Tackling Complexity in the Heart of Software',
     'image_url': 'https://m.media-amazon.com/images/I/51sZW87slRL._SX375_BO1,204,203,200_.jpg',
     'attributes': {'author': 'Eric Evans', 'isbn': '978-0-321-12521-7'}},
]

for b in books:
    cat = get_cat(b.pop('category'))
    brand_name = b.pop('brand')
    brand = brand_map.get(brand_name)
    obj, created = ProductModel.objects.get_or_create(
        name=b['name'],
        product_type=book_type,
        defaults={**b, 'category': cat, 'brand': brand},
    )
    print(f'  {"CREATED" if created else "EXISTS"} Book: {obj.name}')

# ── Clothes (migrated from old bookstore_clothes data) ──
clothes = [
    {'name': 'Nike Dri-FIT T-Shirt', 'price': vnd_price(29.99), 'stock': 50, 'category': 'Sportswear', 'brand': 'Nike',
     'description': 'Lightweight moisture-wicking training tee',
     'image_url': 'https://static.nike.com/a/images/c_limit,w_592,f_auto/t_product_v1/e1c72b15-4f3e-4a53-8bf0-4be6a8d1e6d0/dri-fit-t-shirt.jpg',
     'attributes': {'size': 'M', 'color': 'Black', 'material': 'Polyester'}},
    {'name': 'Adidas Running Shorts', 'price': vnd_price(34.99), 'stock': 35, 'category': 'Sportswear', 'brand': 'Adidas',
     'description': 'Breathable running shorts with zip pocket',
     'image_url': 'https://assets.adidas.com/images/h_840,f_auto,q_auto,fl_lossy,c_fill,g_auto/shorts.jpg',
     'attributes': {'size': 'L', 'color': 'Navy', 'material': 'Nylon'}},
    {'name': 'Uniqlo Flannel Shirt', 'price': vnd_price(39.99), 'stock': 25, 'category': 'Fashion', 'brand': 'Uniqlo',
     'description': 'Soft brushed flannel casual shirt',
     'image_url': 'https://image.uniqlo.com/UQ/ST3/WesternCommon/imagesgoods/flannel.jpg',
     'attributes': {'size': 'M', 'color': 'Red Plaid', 'material': 'Cotton'}},
    {'name': 'Zara Slim Fit Jeans', 'price': vnd_price(49.99), 'stock': 30, 'category': 'Fashion', 'brand': 'Zara',
     'description': 'Classic slim fit denim jeans',
     'image_url': 'https://static.zara.net/photos/2023/I/0/1/p/5575/330/407/2/jeans.jpg',
     'attributes': {'size': '32', 'color': 'Dark Blue', 'material': 'Denim'}},
    {'name': 'H&M Basic Hoodie', 'price': vnd_price(24.99), 'stock': 40, 'category': 'Fashion', 'brand': 'H&M',
     'description': 'Cozy pullover hoodie with kangaroo pocket',
     'image_url': 'https://lp2.hm.com/hmgoepprod?set=quality%5B79%5D&call=url%5Bfile:/hoodie.jpg%5D',
     'attributes': {'size': 'L', 'color': 'Gray', 'material': 'Cotton Blend'}},
    {'name': 'Nike Air Max Sneakers', 'price': vnd_price(129.99), 'stock': 15, 'category': 'Sportswear', 'brand': 'Nike',
     'description': 'Classic Air Max cushioning for everyday comfort',
     'image_url': 'https://static.nike.com/a/images/c_limit,w_592,f_auto/air-max.jpg',
     'attributes': {'size': '42', 'color': 'White/Black', 'material': 'Synthetic'}},
    {'name': 'Adidas Track Jacket', 'price': vnd_price(69.99), 'stock': 20, 'category': 'Sportswear', 'brand': 'Adidas',
     'description': 'Classic 3-stripe track jacket',
     'image_url': 'https://assets.adidas.com/images/h_840,f_auto,q_auto/track-jacket.jpg',
     'attributes': {'size': 'M', 'color': 'Black/White', 'material': 'Recycled Polyester'}},
    {'name': 'Uniqlo Ultra Light Down Jacket', 'price': vnd_price(79.99), 'stock': 18, 'category': 'Fashion', 'brand': 'Uniqlo',
     'description': 'Packable ultra-light down insulated jacket',
     'image_url': 'https://image.uniqlo.com/UQ/ST3/WesternCommon/imagesgoods/down-jacket.jpg',
     'attributes': {'size': 'L', 'color': 'Olive', 'material': 'Nylon/Down'}},
]

for c in clothes:
    cat = get_cat(c.pop('category'))
    brand_name = c.pop('brand')
    brand = brand_map.get(brand_name)
    obj, created = ProductModel.objects.get_or_create(
        name=c['name'],
        product_type=clothes_type,
        defaults={**c, 'category': cat, 'brand': brand},
    )
    print(f'  {"CREATED" if created else "EXISTS"} Clothes: {obj.name}')

print(f'\nTotal products: {ProductModel.objects.count()}')
print(f'  Books: {ProductModel.objects.filter(product_type__name="Book").count()}')
print(f'  Clothes: {ProductModel.objects.filter(product_type__name="Clothes").count()}')
