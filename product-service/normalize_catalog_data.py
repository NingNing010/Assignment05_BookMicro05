import os
from decimal import Decimal

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.db import connection
from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.brand_model import BrandModel

CATEGORY_RENAMES = {
    'Sach Khoa hoc': 'Sách Khoa học',
    'Sach Lap trinh': 'Sách Lập trình',
    'Thoi trang Nam': 'Thời trang Nam',
    'Thoi trang The thao': 'Thời trang Thể thao',
    'Dien thoai thong minh': 'Điện thoại thông minh',
    'May tinh xach tay': 'Máy tính xách tay',
    'My pham': 'Mỹ phẩm',
    'Noi that': 'Nội thất',
    'May anh': 'Máy ảnh',
    'Do choi': 'Đồ chơi',
    'Van phong pham': 'Văn phòng phẩm',
    'Trang suc': 'Trang sức',
    'Do the thao': 'Đồ thể thao',
    'Do cho thu cung': 'Đồ cho thú cưng',
    'Nhac cu': 'Nhạc cụ',
    'Cong cu xay dung': 'Công cụ xây dựng',
    'Thuc pham': 'Thực phẩm',
}

BRAND_RENAMES = {
    'OReilly': "O'Reilly",
    'LOreal': "L'Oréal",
    'NXB Tre': 'NXB Trẻ',
    'Nhieu tac gia': 'Nhiều tác giả',
}

NAME_RENAMES = {
    'Vu tru hoc co ban': 'Vũ trụ học cơ bản',
    'Sapiens Luoc su loai nguoi': 'Sapiens: Lược sử loài người',
    'Tu dien Y hoc': 'Từ điển Y học',
    'Sinh hoc dai cuong': 'Sinh học đại cương',
    'Vat ly luong tu': 'Vật lý lượng tử',
    'Ao khoac gio': 'Áo khoác gió',
    'Ao thun co ban': 'Áo thun cơ bản',
    'Quan Jeans Slim-fit': 'Quần Jeans Slim-fit',
    'Ao so mi dai tay': 'Áo sơ mi dài tay',
    'Ao len co lo': 'Áo len cổ lọ',
    'Ao chay bo Dri-Fit': 'Áo chạy bộ Dri-Fit',
    'Quan dui chay': 'Quần đùi chạy',
    'Bo the thao thu dong': 'Bộ thể thao thu đông',
    'Ao tank top gym': 'Áo tank top tập gym',
    'Ao khoac chong gio': 'Áo khoác chống gió',
    'Ban lam viec LINNMON': 'Bàn làm việc LINNMON',
    'Ghe xoay MARKUS': 'Ghế xoay MARKUS',
    'Tu quan ao PAX': 'Tủ quần áo PAX',
    'Giuong doi MALM': 'Giường đôi MALM',
    'Ke sach BILLY': 'Kệ sách BILLY',
    'Piano Dien P-45': 'Đàn Piano Điện P-45',
    'Guitar Classic C40': 'Đàn Guitar Classic C40',
    'Acoustic F310': 'Đàn Acoustic F310',
    'Sao dien tu Venova': 'Sáo điện tử Venova',
    'May khoan dong luc': 'Máy khoan động lực',
    'May mai goc GWS': 'Máy mài góc GWS',
    'Bo van vit 32 mon': 'Bộ vặn vít 32 món',
    'May cua long GST': 'Máy cưa lọng GST',
    'May rua xe cao ap': 'Máy rửa xe cao áp',
    'Banh quy Oreo Vani': 'Bánh quy Oreo Vani',
    'Oreo Dau tay': 'Oreo Dâu tây',
    'Oreo Socola': 'Oreo Socola',
    'Oreo Matcha': 'Oreo Matcha',
    'Banh xop Oreo': 'Bánh xốp Oreo',
    'Kem chong nang UV': 'Kem chống nắng UV',
    'Tay trang Micellar': 'Tẩy trang Micellar',
    'Kem duong cap am': 'Kem dưỡng cấp ẩm',
    'Son thoi do cam': 'Son thỏi đỏ cam',
    'Serum Vitamin C': 'Serum Vitamin C',
    'So tay Classic A5': 'Sổ tay Classic A5',
    'So Bullet Journal': 'Sổ Bullet Journal',
    'So phac thao Art': 'Sổ phác thảo Art',
    'But bi Moleskine': 'Bút bi Moleskine',
    'Giay chay Pegasus 40': 'Giày chạy Pegasus 40',
    'Giay bong ro LeBron 20': 'Giày bóng rổ LeBron 20',
    'Tui trong the thao': 'Túi trống thể thao',
    'Bong da Premier': 'Bóng đá Premier',
    'Balo Nike Air': 'Balo Nike Air',
}

ATTRIBUTE_RENAMES = {
    'Trang': 'Trắng',
    'Trang/Den': 'Trắng/Đen',
    'Go cong nghiep': 'Gỗ công nghiệp',
    'Bac/Pha le': 'Bạc/Pha lê',
    'Phap': 'Pháp',
    'Moi loai da': 'Mọi loại da',
    'Chay bo / Da nang': 'Chạy bộ / Đa năng',
    'Phim / Day': 'Phím / Dây',
    'Go / Den': 'Gỗ / Đen',
    'Normal': 'Normal',
    'Sweet': 'Sweet',
    'No': 'No',
    'Yes': 'Yes',
}


def ensure_image_url_longtext():
    with connection.cursor() as cursor:
        cursor.execute("SHOW COLUMNS FROM catalog_product LIKE 'image_url'")
        row = cursor.fetchone()
        if not row:
            return
        column_type = str(row[1]).lower()
        if 'text' in column_type:
            return
        cursor.execute("ALTER TABLE catalog_product MODIFY COLUMN image_url LONGTEXT NOT NULL")


def normalize_price(value):
    try:
        numeric = Decimal(str(value))
    except Exception:
        return value
    if numeric <= 0:
        return value
    if numeric >= 100000:
        normalized = int(round(float(numeric) / 100.0))
        return Decimal(normalized)
    return value


def normalize_attributes(attributes):
    if not isinstance(attributes, dict):
        return attributes
    normalized = {}
    for key, val in attributes.items():
        if isinstance(val, str):
            normalized[key] = ATTRIBUTE_RENAMES.get(val, val)
        else:
            normalized[key] = val
    return normalized


def rebuild_description(product):
    category = product.category.name if product.category else 'Sản phẩm'
    brand = product.brand.name if product.brand else 'thương hiệu'
    return f'Sản phẩm {product.name} chính hãng từ {brand}. {category} chất lượng cao.'


def main():
    ensure_image_url_longtext()

    for category in CategoryModel.objects.all():
        new_name = CATEGORY_RENAMES.get(category.name)
        if new_name and new_name != category.name:
            category.name = new_name
            if not category.description or category.description == category.name:
                category.description = f'Danh mục {new_name}'
            category.save(update_fields=['name', 'description'])

    for brand in BrandModel.objects.all():
        new_name = BRAND_RENAMES.get(brand.name)
        if new_name and new_name != brand.name:
            brand.name = new_name
            brand.save(update_fields=['name'])

    updated = 0
    for product in ProductModel.objects.select_related('category', 'brand').all():
        changed = False

        new_name = NAME_RENAMES.get(product.name)
        if new_name and new_name != product.name:
            product.name = new_name
            changed = True

        normalized_price = normalize_price(product.price)
        if normalized_price != product.price:
            product.price = normalized_price
            changed = True

        normalized_attributes = normalize_attributes(product.attributes or {})
        if normalized_attributes != (product.attributes or {}):
            product.attributes = normalized_attributes
            changed = True

        new_description = rebuild_description(product)
        if product.description != new_description:
            product.description = new_description
            changed = True

        if changed:
            product.save()
            updated += 1

    print(f'Normalized {updated} products.')
    print(f'Categories: {list(CategoryModel.objects.values_list("name", flat=True))}')
    print(f'Brands: {list(BrandModel.objects.values_list("name", flat=True))}')


if __name__ == '__main__':
    main()
