"""
Rich seed data for the unified product-service.

Run inside the container:
    python modules/catalog/seeds/massive_products_seed.py

This script resets catalog data and repopulates:
- product types
- categories
- brands
- products across many categories
- a few product variants
"""
from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django

django.setup()

from modules.catalog.infrastructure.models.brand_model import BrandModel
from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel
from modules.catalog.infrastructure.models.variant_model import VariantModel


def money(value: str) -> Decimal:
    return Decimal(value)


def ensure_type(name: str, description: str = ''):
    return ProductTypeModel.objects.get_or_create(name=name, defaults={'description': description})[0]


def ensure_category(name: str, description: str = '', parent=None):
    return CategoryModel.objects.get_or_create(
        name=name,
        defaults={'description': description, 'parent': parent},
    )[0]


def ensure_brand(name: str, description: str = '', address: str = '', email: str = ''):
    defaults = {'description': description, 'address': address, 'email': email}
    return BrandModel.objects.get_or_create(name=name, defaults=defaults)[0]


def upsert_product(*, name: str, product_type, category, brand, price: str, stock: int,
                   description: str, image_url: str, attributes: dict):
    obj, _ = ProductModel.objects.update_or_create(
        name=name,
        product_type=product_type,
        defaults={
            'category': category,
            'brand': brand,
            'price': money(price),
            'stock': stock,
            'description': description,
            'image_url': image_url,
            'attributes': attributes,
        },
    )
    return obj


def seed_variants(product, variants):
    VariantModel.objects.filter(product=product).delete()
    for variant in variants:
        VariantModel.objects.create(product=product, **variant)


def generate_products():
    print('Resetting catalog data...')
    VariantModel.objects.all().delete()
    ProductModel.objects.all().delete()
    BrandModel.objects.all().delete()
    CategoryModel.objects.all().delete()
    ProductTypeModel.objects.all().delete()

    book = ensure_type('Book', 'Printed books and e-books')
    clothes = ensure_type('Clothes', 'Wearables and fashion items')
    electronics = ensure_type('Electronics', 'Phones, laptops, and accessories')
    home = ensure_type('Home', 'Furniture and household products')
    beauty = ensure_type('Beauty', 'Cosmetics and personal care')
    sports = ensure_type('Sports', 'Sporting goods and training gear')

    root_groups = {
        'Books': ensure_category('Books', 'Books and reading materials'),
        'Fashion': ensure_category('Fashion', 'Clothing and apparel'),
        'Electronics': ensure_category('Electronics', 'Electronic devices and gadgets'),
        'Home & Living': ensure_category('Home & Living', 'Home, kitchen, and decor'),
        'Beauty': ensure_category('Beauty', 'Beauty and personal care'),
        'Sports': ensure_category('Sports', 'Sportswear and equipment'),
    }

    subcategories = {
        'Programming': ensure_category('Programming', 'Programming books', root_groups['Books']),
        'Architecture': ensure_category('Architecture', 'Architecture and design books', root_groups['Books']),
        'Business': ensure_category('Business', 'Business and management books', root_groups['Books']),
        'Data Science': ensure_category('Data Science', 'Data, AI, and machine learning books', root_groups['Books']),
        'Men': ensure_category('Men', 'Menswear', root_groups['Fashion']),
        'Women': ensure_category('Women', 'Womenswear', root_groups['Fashion']),
        'Running': ensure_category('Running', 'Running gear', root_groups['Sports']),
        'Home Office': ensure_category('Home Office', 'Home office and workspace', root_groups['Home & Living']),
        'Kitchen': ensure_category('Kitchen', 'Kitchen products', root_groups['Home & Living']),
        'Skincare': ensure_category('Skincare', 'Skin care products', root_groups['Beauty']),
        'Mobile': ensure_category('Mobile', 'Mobile devices and accessories', root_groups['Electronics']),
        'Laptop': ensure_category('Laptop', 'Laptops and notebooks', root_groups['Electronics']),
    }

    brands = {
        'O\'Reilly Media': ensure_brand('O\'Reilly Media', 'Technical publishing house', 'Sebastopol, CA', 'info@oreilly.com'),
        'Pearson': ensure_brand('Pearson', 'Global education publisher', 'London, UK', 'info@pearson.com'),
        'Manning': ensure_brand('Manning', 'Engineering books publisher', 'New York, USA', 'info@manning.com'),
        'Nike': ensure_brand('Nike', 'Sportswear brand', email='support@nike.com'),
        'Adidas': ensure_brand('Adidas', 'Sportswear brand', email='support@adidas.com'),
        'Uniqlo': ensure_brand('Uniqlo', 'Casual fashion brand'),
        'Zara': ensure_brand('Zara', 'Fast-fashion brand'),
        'Apple': ensure_brand('Apple', 'Consumer electronics brand'),
        'Samsung': ensure_brand('Samsung', 'Consumer electronics brand'),
        'Dell': ensure_brand('Dell', 'Computing hardware brand'),
        'IKEA': ensure_brand('IKEA', 'Furniture and home living brand'),
        'L\'Oreal': ensure_brand('L\'Oreal', 'Beauty and cosmetics brand'),
        'Innisfree': ensure_brand('Innisfree', 'Natural skincare brand'),
        'Bosch': ensure_brand('Bosch', 'Tools and appliances brand'),
        'LEGO': ensure_brand('LEGO', 'Educational toy brand'),
        'Yamaha': ensure_brand('Yamaha', 'Musical instruments brand'),
        'Swarovski': ensure_brand('Swarovski', 'Jewelry and accessories brand'),
        'Royal Canin': ensure_brand('Royal Canin', 'Pet food brand'),
    }

    products = [
        {
            'name': 'Clean Code', 'product_type': book, 'category': subcategories['Programming'], 'brand': brands['Pearson'],
            'price': '390000', 'stock': 15,
            'description': 'A Handbook of Agile Software Craftsmanship by Robert C. Martin',
            'image_url': 'https://m.media-amazon.com/images/I/41xShlnTZTL._SX376_BO1,204,203,200_.jpg',
            'attributes': {'author': 'Robert C. Martin', 'isbn': '978-0132350884', 'pages': 464, 'language': 'English'},
            'variants': [
                {'sku': 'BOOK-CLEANCODE-HC', 'size': 'Hardcover', 'color': '', 'price_override': money('420000'), 'stock': 8},
                {'sku': 'BOOK-CLEANCODE-PB', 'size': 'Paperback', 'color': '', 'price_override': money('390000'), 'stock': 7},
            ],
        },
        {
            'name': 'Design Patterns', 'product_type': book, 'category': subcategories['Architecture'], 'brand': brands['Pearson'],
            'price': '510000', 'stock': 10,
            'description': 'Elements of Reusable Object-Oriented Software',
            'image_url': 'https://m.media-amazon.com/images/I/51szD9HC9pL._SX395_BO1,204,203,200_.jpg',
            'attributes': {'author': 'Gang of Four', 'isbn': '978-0201633610', 'pages': 395, 'language': 'English'},
            'variants': [],
        },
        {
            'name': 'Domain-Driven Design', 'product_type': book, 'category': subcategories['Architecture'], 'brand': brands['Pearson'],
            'price': '560000', 'stock': 7,
            'description': 'Tackling Complexity in the Heart of Software',
            'image_url': 'https://m.media-amazon.com/images/I/51sZW87slRL._SX375_BO1,204,203,200_.jpg',
            'attributes': {'author': 'Eric Evans', 'isbn': '978-0321125217', 'pages': 560, 'language': 'English'},
            'variants': [],
        },
        {
            'name': 'Hands-On Machine Learning', 'product_type': book, 'category': subcategories['Data Science'], 'brand': brands['O\'Reilly Media'],
            'price': '620000', 'stock': 8,
            'description': 'Practical machine learning book with examples',
            'image_url': 'https://m.media-amazon.com/images/I/51aqYc1QyrL._SX379_BO1,204,203,200_.jpg',
            'attributes': {'author': 'Aurélien Géron', 'isbn': '978-1492032649', 'pages': 936, 'language': 'English'},
            'variants': [],
        },
        {
            'name': 'The Pragmatic Programmer', 'product_type': book, 'category': subcategories['Programming'], 'brand': brands['Manning'],
            'price': '470000', 'stock': 12,
            'description': 'Your Journey to Mastery, 20th Anniversary Edition',
            'image_url': 'https://m.media-amazon.com/images/I/51cUVaBWZzL._SX380_BO1,204,203,200_.jpg',
            'attributes': {'author': 'David Thomas, Andrew Hunt', 'isbn': '978-0135957059', 'pages': 352, 'language': 'English'},
            'variants': [],
        },
        {
            'name': 'Nike Dri-FIT Training Tee', 'product_type': clothes, 'category': subcategories['Men'], 'brand': brands['Nike'],
            'price': '290000', 'stock': 50,
            'description': 'Lightweight moisture-wicking training tee',
            'image_url': 'https://static.nike.com/a/images/c_limit,w_592,f_auto/t_product_v1/e1c72b15-4f3e-4a53-8bf0-4be6a8d1e6d0/dri-fit-t-shirt.jpg',
            'attributes': {'size': 'M', 'color': 'Black', 'material': 'Polyester', 'fit': 'Regular'},
            'variants': [
                {'sku': 'CLT-NIKE-TEE-M', 'size': 'M', 'color': 'Black', 'price_override': money('290000'), 'stock': 18},
                {'sku': 'CLT-NIKE-TEE-L', 'size': 'L', 'color': 'Black', 'price_override': money('290000'), 'stock': 16},
                {'sku': 'CLT-NIKE-TEE-XL', 'size': 'XL', 'color': 'Black', 'price_override': money('290000'), 'stock': 16},
            ],
        },
        {
            'name': 'Adidas Running Shorts', 'product_type': clothes, 'category': subcategories['Running'], 'brand': brands['Adidas'],
            'price': '340000', 'stock': 35,
            'description': 'Breathable running shorts with zip pocket',
            'image_url': 'https://assets.adidas.com/images/h_840,f_auto,q_auto,fl_lossy,c_fill,g_auto/shorts.jpg',
            'attributes': {'size': 'L', 'color': 'Navy', 'material': 'Nylon', 'fit': 'Slim'},
            'variants': [],
        },
        {
            'name': 'Uniqlo Flannel Shirt', 'product_type': clothes, 'category': subcategories['Men'], 'brand': brands['Uniqlo'],
            'price': '399000', 'stock': 25,
            'description': 'Soft brushed flannel casual shirt',
            'image_url': 'https://image.uniqlo.com/UQ/ST3/WesternCommon/imagesgoods/flannel.jpg',
            'attributes': {'size': 'M', 'color': 'Red Plaid', 'material': 'Cotton'},
            'variants': [],
        },
        {
            'name': 'Zara Slim Fit Jeans', 'product_type': clothes, 'category': subcategories['Women'], 'brand': brands['Zara'],
            'price': '499000', 'stock': 30,
            'description': 'Classic slim fit denim jeans',
            'image_url': 'https://static.zara.net/photos/2023/I/0/1/p/5575/330/407/2/jeans.jpg',
            'attributes': {'size': '32', 'color': 'Dark Blue', 'material': 'Denim'},
            'variants': [],
        },
        {
            'name': 'Apple iPhone 15 Pro Max', 'product_type': electronics, 'category': subcategories['Mobile'], 'brand': brands['Apple'],
            'price': '32990000', 'stock': 14,
            'description': 'Latest flagship smartphone from Apple',
            'image_url': 'https://store.storeimages.cdn-apple.com/8756/as-images.apple.com/is/iphone-15-pro-finish-select-202309-6-7inch-naturaltitanium?wid=5120&hei=2880&fmt=p-jpg',
            'attributes': {'ram': '8GB', 'storage': '256GB', 'screen': 'OLED 6.7 inch', 'color': 'Natural Titanium'},
            'variants': [
                {'sku': 'APL-IP15PM-256-NAT', 'size': '', 'color': 'Natural Titanium', 'price_override': money('32990000'), 'stock': 6},
                {'sku': 'APL-IP15PM-256-BLK', 'size': '', 'color': 'Black Titanium', 'price_override': money('32990000'), 'stock': 8},
            ],
        },
        {
            'name': 'Samsung Galaxy S24 Ultra', 'product_type': electronics, 'category': subcategories['Mobile'], 'brand': brands['Samsung'],
            'price': '28990000', 'stock': 16,
            'description': 'Android flagship with S Pen support',
            'image_url': 'https://images.samsung.com/is/image/samsung/p6pim/vn/2401/gallery/vn-galaxy-s24-s928-sm-s928bztqxxv-539325497',
            'attributes': {'ram': '12GB', 'storage': '512GB', 'battery': '5000mAh', 'color': 'Titanium Gray'},
            'variants': [],
        },
        {
            'name': 'Dell XPS 15 9530', 'product_type': electronics, 'category': subcategories['Laptop'], 'brand': brands['Dell'],
            'price': '42990000', 'stock': 9,
            'description': 'High-end productivity laptop for creators',
            'image_url': 'https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/xps-notebooks/15-9530/media-gallery/silver/notebook-xps-15-9530-t-silver-gallery-2.psd?fmt=png-alpha&wid=1000',
            'attributes': {'cpu': 'Intel Core i7 13th Gen', 'ram': '16GB', 'ssd': '1TB', 'gpu': 'RTX 4050'},
            'variants': [],
        },
        {
            'name': 'MacBook Pro 14 M3', 'product_type': electronics, 'category': subcategories['Laptop'], 'brand': brands['Apple'],
            'price': '52990000', 'stock': 6,
            'description': 'Portable professional laptop with Apple Silicon',
            'image_url': 'https://store.storeimages.cdn-apple.com/8756/as-images.apple.com/is/mbp14-spacegray-select-202310?wid=904&hei=840&fmt=jpeg',
            'attributes': {'cpu': 'Apple M3', 'ram': '16GB', 'storage': '512GB', 'color': 'Space Gray'},
            'variants': [],
        },
        {
            'name': 'IKEA LINNMON Desk', 'product_type': home, 'category': subcategories['Home Office'], 'brand': brands['IKEA'],
            'price': '1890000', 'stock': 20,
            'description': 'Minimal home office desk',
            'image_url': 'https://www.ikea.com/global/assets/navigation/images/desks-computer-desks-20649.jpeg',
            'attributes': {'material': 'Particle board', 'color': 'White', 'assembly_needed': True},
            'variants': [],
        },
        {
            'name': 'Bosch Drill Set', 'product_type': home, 'category': subcategories['Home Office'], 'brand': brands['Bosch'],
            'price': '1490000', 'stock': 22,
            'description': 'Cordless drill and accessory set',
            'image_url': 'https://www.bosch-pt.com.vn/vn/media/ptng_images/product_images/gsb_16_re_professional/gsb_16_re_professional_06012281l2_product_1_image_main.jpg',
            'attributes': {'power': '600W', 'cordless': 'No', 'warranty': '1 Year'},
            'variants': [],
        },
        {
            'name': 'Loreal UV Defender', 'product_type': beauty, 'category': subcategories['Skincare'], 'brand': brands['L\'Oreal'],
            'price': '250000', 'stock': 55,
            'description': 'Daily sunscreen with broad spectrum protection',
            'image_url': 'https://www.loreal.com/-/media/project/loreal/brand-sites/corp/master/lcorp/articles/loreal-paris/uv-defender/loreal-paris-uv-defender-card.jpg',
            'attributes': {'volume': '50ml', 'skin_type': 'All skin types', 'origin': 'France'},
            'variants': [],
        },
        {
            'name': 'Innisfree Green Tea Serum', 'product_type': beauty, 'category': subcategories['Skincare'], 'brand': brands['Innisfree'],
            'price': '420000', 'stock': 32,
            'description': 'Hydrating serum for daily skincare routine',
            'image_url': 'https://vn.innisfree.com/cdn/shop/files/BtsS_2_1000x.png',
            'attributes': {'volume': '80ml', 'skin_type': 'Oily skin', 'organic': True},
            'variants': [],
        },
        {
            'name': 'LEGO Millennium Falcon', 'product_type': sports, 'category': root_groups['Sports'], 'brand': brands['LEGO'],
            'price': '8490000', 'stock': 5,
            'description': 'Collector set for display and creative building',
            'image_url': 'https://www.lego.com/cdn/cs/set/assets/blt1f2d26d57cc178d8/75192.jpg',
            'attributes': {'pieces': 7510, 'age_rating': '16+', 'material': 'ABS plastic'},
            'variants': [],
        },
        {
            'name': 'Yamaha P-45 Digital Piano', 'product_type': home, 'category': subcategories['Home Office'], 'brand': brands['Yamaha'],
            'price': '11990000', 'stock': 4,
            'description': '88-key digital piano for home and stage use',
            'image_url': 'https://vn.yamaha.com/vi/products/contents/keyboards/p_series/images/p-45_b_01.jpg',
            'attributes': {'instrument_type': 'Keyboard', 'color': 'Black', 'keys': 88},
            'variants': [],
        },
        {
            'name': 'Swarovski Swan Necklace', 'product_type': home, 'category': subcategories['Women'], 'brand': brands['Swarovski'],
            'price': '2990000', 'stock': 11,
            'description': 'Elegant necklace for formal occasions',
            'image_url': 'https://www.swarovski.com/on/demandware.static/-/Sites-swarovski-master-catalog/default/dweabf7ad6/images/swa/5007735/5007735.jpg',
            'attributes': {'material': 'Silver', 'gem': 'Swarovski Crystal', 'color': 'Silver'},
            'variants': [],
        },
        {
            'name': 'Royal Canin Kitten Dry Food', 'product_type': home, 'category': subcategories['Kitchen'], 'brand': brands['Royal Canin'],
            'price': '350000', 'stock': 40,
            'description': 'Complete nutrition for kittens',
            'image_url': 'https://www.royalcanin.com/vn/media/16140/kitten-dry-packshot.png',
            'attributes': {'weight': '2kg', 'flavor': 'Chicken', 'pet_type': 'Cat'},
            'variants': [],
        },
    ]

    total_created = 0
    for item in products:
        variants = item.pop('variants')
        product = upsert_product(**item)
        seed_variants(product, variants)
        total_created += 1

    print(f'Created/updated {total_created} products.')
    print(f'Types: {ProductTypeModel.objects.count()}, Categories: {CategoryModel.objects.count()}, Brands: {BrandModel.objects.count()}, Variants: {VariantModel.objects.count()}')


generate_products()
