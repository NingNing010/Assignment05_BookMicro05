import os
import django
import random
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.brand_model import BrandModel
from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel


def vnd_price(low, high):
    return random.randrange(int(low), int(high) + 1000, 1000)

def generate_products():
    print("Clearing old data (except books/clothes specifically seeded if needed, but wiping table is cleaner)...")
    ProductModel.objects.all().delete()
    CategoryModel.objects.all().delete()
    BrandModel.objects.all().delete()
    ProductTypeModel.objects.all().delete()

    print("Creating core Product Types...")
    type_book, _ = ProductTypeModel.objects.get_or_create(name='Book')
    type_clothes, _ = ProductTypeModel.objects.get_or_create(name='Clothes')
    type_generic, _ = ProductTypeModel.objects.get_or_create(name='Generic')

    categories_data = [
        ("Sách Khoa học", type_book, [
            {"brand": "NXB Trẻ", "items": ["Vũ trụ học cơ bản", "Sapiens Lược sử loài người", "Từ điển Y học"], "attr": {"author": "Nhiều tác giả", "pages": 300}, "img": "https://m.media-amazon.com/images/I/51h5d4dYaoL._SX258_BO1,204,203,200_.jpg"},
            {"brand": "NXB Kim Đồng", "items": ["Khám phá thế giới Động vật", "Bách khoa thư Không gian", "Gen - Trọn bộ"], "attr": {"author": "Khoa học Sinh", "pages": 250}, "img": "https://m.media-amazon.com/images/I/41xShlnTZTL._SX376_BO1,204,203,200_.jpg"}
        ]),
        ("Sách Lập trình", type_book, [
            {"brand": "O'Reilly", "items": ["Clean Code Tiếng Việt", "Design Pattern Căn bản", "Mastering Python", "Docker Deep Dive"], "attr": {"author": "IT Expert", "isbn": "978-0123456"}, "img": "https://m.media-amazon.com/images/I/5131OWtQRaL._SX381_BO1,204,203,200_.jpg"}
        ]),
        ("Thời trang Nam", type_clothes, [
            {"brand": "Uniqlo", "items": ["Áo khoác gió", "Áo thun cơ bản", "Quần Jeans Slim-fit", "Áo sơ mi dài tay"], "attr": {"size": "L", "color": "Navy", "material": "Cotton"}, "img": "https://image.uniqlo.com/UQ/ST3/WesternCommon/imagesgoods/flannel.jpg"},
            {"brand": "Zara", "items": ["Áo len chui đầu", "Quần âu lịch lãm", "Áo Vest mỏng"], "attr": {"size": "M", "color": "Đen", "material": "Wool"}, "img": "https://static.zara.net/photos/2023/I/0/1/p/5575/330/407/2/jeans.jpg"}
        ]),
        ("Thời trang Thể thao", type_clothes, [
            {"brand": "Nike", "items": ["Áo chạy bộ Dri-Fit", "Quần đùi chạy", "Bộ thể thao thu đông"], "attr": {"size": "XL", "color": "Trắng", "technology": "Dri-fit"}, "img": "https://static.nike.com/a/images/c_limit,w_592,f_auto/t_product_v1/e1c72b15-4f3e-4a53-8bf0-4be6a8d1e6d0/dri-fit-t-shirt.jpg"},
            {"brand": "Adidas", "items": ["Áo Polo Golf", "Quần Jogger nỉ", "Set khoác gió Das"], "attr": {"size": "L", "color": "Đen/Trắng", "fit": "Regular"}, "img": "https://assets.adidas.com/images/h_840,f_auto,q_auto/track-jacket.jpg"}
        ]),
        ("Điện thoại thông minh", type_generic, [
            {"brand": "Apple", "items": ["iPhone 15 Pro Max", "iPhone 15", "iPhone 14 Plus", "iPhone 13", "iPhone SE 3", "iPhone 15 Pro"], "attr": {"ram": "8GB", "storage": "256GB", "screen": "OLED 6.7"}, "img": "https://store.storeimages.cdn-apple.com/8756/as-images.apple.com/is/iphone-15-pro-finish-select-202309-6-7inch-naturaltitanium?wid=5120&hei=2880&fmt=p-jpg"},
            {"brand": "Samsung", "items": ["Galaxy S24 Ultra", "Galaxy S23", "Galaxy Z Fold 5", "Galaxy Z Flip 5", "Galaxy A54", "Galaxy Tab S9"], "attr": {"ram": "12GB", "storage": "512GB", "battery": "5000mAh"}, "img": "https://images.samsung.com/is/image/samsung/p6pim/vn/2401/gallery/vn-galaxy-s24-s928-sm-s928bztqxxv-539325497"}
        ]),
        ("Máy tính xách tay", type_generic, [
            {"brand": "Dell", "items": ["XPS 15 9530", "XPS 13 Plus", "Inspiron 16", "Alienware x17", "Latitude 5430", "G15 Gaming"], "attr": {"cpu": "Intel Core i7 13th", "ram": "16GB", "ssd": "1TB"}, "img": "https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/xps-notebooks/15-9530/media-gallery/silver/notebook-xps-15-9530-t-silver-gallery-2.psd?fmt=png-alpha&wid=1000"},
            {"brand": "Apple", "items": ["MacBook Pro 16 M3 Max", "MacBook Air M2 15", "MacBook Pro 14 M3", "MacBook Air M1", "Mac Studio", "Mac mini M2"], "attr": {"cpu": "Apple M-Series", "ram": "16GB", "storage": "512GB"}, "img": "https://store.storeimages.cdn-apple.com/8756/as-images.apple.com/is/mbp14-spacegray-select-202310?wid=904&hei=840&fmt=jpeg"}
        ]),
        ("Mỹ phẩm", type_generic, [
            {"brand": "L'Oreal", "items": ["Kem chống nắng UV", "Tẩy trang Micellar", "Kem dưỡng cấp ẩm", "Son thỏi đỏ cam", "Mascara dài mi", "Serum Vitamin C"], "attr": {"volume": "50ml", "skin_type": "Mọi loại da", "origin": "Pháp"}, "img": "https://www.loreal.com/-/media/project/loreal/brand-sites/corp/master/lcorp/articles/loreal-paris/uv-defender/loreal-paris-uv-defender-card.jpg"},
            {"brand": "Innisfree", "items": ["Sữa rửa mặt Trà Tuyết", "Nước cân bằng Jeju", "Mặt nạ đất sét", "Kem mắt Green Tea"], "attr": {"volume": "150ml", "skin_type": "Da dầu mụn", "organic": "Yes"}, "img": "https://vn.innisfree.com/cdn/shop/files/BtsS_2_1000x.png"}
        ]),
        ("Nội thất", type_generic, [
            {"brand": "IKEA", "items": ["Bàn làm việc LINNMON", "Ghế xoay MARKUS", "Tủ quần áo PAX", "Giường đôi MALM", "Kệ sách BILLY", "Sofa KLIPPAN"], "attr": {"material": "Gỗ công nghiệp", "color": "Trắng/Đen", "assembly_needed": "Yes"}, "img": "https://www.ikea.com/global/assets/navigation/images/desks-computer-desks-20649.jpeg"}
        ]),
        ("Máy ảnh", type_generic, [
            {"brand": "Sony", "items": ["Alpha a7 IV", "Alpha a6700", "ZV-E10 Vlog", "FX3 Cinema", "Cyber-shot RX100"], "attr": {"sensor": "Full-frame", "megapixels": "33MP", "lens_mount": "Sony E"}, "img": "https://www.sony.com.vn/image/a0a1a069a3a8d6e3cda83ff26bbce5c9?fmt=pjpeg&bgcolor=FFFFFF&bgc=FFFFFF&wid=2520&hei=1080"},
            {"brand": "Canon", "items": ["EOS R5", "EOS R6 Mark II", "EOS RP", "EOS 90D"], "attr": {"sensor": "Full-frame", "resolution": "45MP", "video": "8K RAW"}, "img": "https://vn.canon/media/image/2020/07/06/b8a05a8b50e34c0aa0ee33146e4c7ba9_EOS+R5+Front+Slant.png"}
        ]),
        ("Đồ chơi", type_generic, [
            {"brand": "LEGO", "items": ["Tàu Millennium Falcon", "Porsche 911 GT3", "Lâu đài Hogwarts", "Lego City Police", "Lego Ninjago Dragon", "Kiến trúc tháp Eiffel"], "attr": {"pieces": 1500, "age_rating": "12+", "material": "Nhựa ABS"}, "img": "https://www.lego.com/cdn/cs/set/assets/blt1f2d26d57cc178d8/75192.jpg"}
        ]),
        ("Văn phòng phẩm", type_generic, [
            {"brand": "Moleskine", "items": ["Sổ tay Classic A5", "Sổ Bullet Journal", "Sổ phác thảo Art", "Bút bi Moleskine"], "attr": {"paper_type": "Blank/Lined", "pages": 240, "cover": "Hardcover"}, "img": "https://www.moleskine.vn/wp-content/uploads/2021/04/Moleskine-Classic-Notebook-Hard-Cover-Large-Black.jpg"},
            {"brand": "Lamy", "items": ["Bút mực Safari Đỏ", "Bút mực AL-Star", "Bút bi Joy Calligraphy"], "attr": {"nib": "Thép mạ F", "color": "Đa dạng"}, "img": "https://lamy.vn/wp-content/uploads/2016/11/safari.jpg"}
        ]),
        ("Trang sức", type_generic, [
            {"brand": "Swarovski", "items": ["Dây chuyền Thiên nga", "Khuyên tai Iconic", "Lắc tay pha lê", "Nhẫn kim cương", "Vòng cổ ánh sao", "Bộ trang sức Cưới"], "attr": {"material": "Bạc/Pha lê", "color": "Bạch kim", "gem": "Swarovski Crystal"}, "img": "https://www.swarovski.com/on/demandware.static/-/Sites-swarovski-master-catalog/default/dweabf7ad6/images/swa/5007735/5007735.jpg"}
        ]),
        ("Đồ thể thao", type_generic, [
            {"brand": "Nike", "items": ["Giày chạy Pegasus 40", "Giày bóng rổ LeBron 20", "Túi trống thể thao", "Bóng đá Premier 24", "Balo Nike Air", "Kính bơi Nike"], "attr": {"sport": "Chạy bộ / Đa năng", "size": "US 9"}, "img": "https://static.nike.com/a/images/c_limit,w_592,f_auto/t_product_v1/a0d1gxc7tmtuudwq9xks/pegasus-40-mens-road-running-shoes-MCV0fX.png"}
        ]),
        ("Đồ cho thú cưng", type_generic, [
            {"brand": "Royal Canin", "items": ["Thức ăn hạt cho Mèo", "Thức ăn hạt Poodle", "Pate mèo con", "Thức ăn kiêng chó lớn"], "attr": {"weight": "2kg", "flavor": "Meat", "pet_type": "Mèo/Chó"}, "img": "https://www.royalcanin.com/vn/media/16140/kitten-dry-packshot.png"}
        ]),
        ("Nhạc cụ", type_generic, [
            {"brand": "Yamaha", "items": ["Đàn Piano Điện P-45", "Guitar Classic C40", "Acoustic F310", "Sáo điện tử Venova", "Trống điện tử DTX402", "Organ PSR-E473"], "attr": {"instrument_type": "Phím / Dây", "color": "Gỗ / Đen"}, "img": "https://vn.yamaha.com/vi/products/contents/keyboards/p_series/images/p-45_b_01.jpg"}
        ]),
        ("Công cụ xây dựng", type_generic, [
            {"brand": "Bosch", "items": ["Máy khoan động lực", "Máy mài góc GWS", "Bộ vặn vít 32 món", "Máy cưa lọng GST", "Máy 12V gia đình", "Máy rửa xe cao áp"], "attr": {"power": "600W", "cordless": "No", "warranty": "1 Year"}, "img": "https://www.bosch-pt.com.vn/vn/media/ptng_images/product_images/gsb_16_re_professional/gsb_16_re_professional_06012281l2_product_1_image_main.jpg"}
        ]),
        ("Thực phẩm", type_generic, [
            {"brand": "Oreo", "items": ["Bánh quy Oreo Vani", "Oreo Dâu tây", "Oreo Socola", "Oreo Matcha", "Oreo Kem Lạnh", "Bánh xốp Oreo O's"], "attr": {"weight": "137g", "flavor": "Sweet", "diet": "Normal"}, "img": "https://product.hstatic.net/200000305145/product/oreo-vani-137g_1c3bf7e1f1bb44ddbfbb250dcad891e4_master.jpg"}
        ])
    ]

    total_created = 0
    for cat_name, product_type, product_groups in categories_data:
        cat, _ = CategoryModel.objects.get_or_create(name=cat_name, description=f"Danh mục {cat_name}")
        for group in product_groups:
            brand, _ = BrandModel.objects.get_or_create(name=group["brand"])
            items = group["items"]
            # Ensure we have enough items by duplicating with variants if necessary to hit ~225+
            suffixes = ["", " Pro", " Plus", " Max", " Ultra", " Lite"]
            for item in items:
                for suffix in suffixes:
                    name = f"{item}{suffix}"
                    # Just to avoid identical pricing
                    price = vnd_price(150000, 5000000)
                    stock = random.randint(0, 150)
                    
                    # Special pricing adjustments
                    if "iPhone" in name or "MacBook" in name or "XPS" in name or "Máy ảnh" in name or "Piano" in name:
                        price = vnd_price(3000000, 35000000)
                    if "Oreo" in name or "Bút" in name or "Notebook" in name:
                        price = vnd_price(10000, 250000)

                    ProductModel.objects.create(
                        name=name,
                        description=f"Sản phẩm {name} chính hãng từ {brand.name}. {cat_name} chất lượng cao.",
                        price=price,
                        stock=stock,
                        image_url=group["img"],
                        category=cat,
                        brand=brand,
                        product_type=product_type,
                        attributes=group["attr"]
                    )
                    total_created += 1

    print(f"✅ Đã tạo thành công {total_created} sản phẩm thuộc {len(categories_data)} danh mục lớn.")
    print("Mọi sản phẩm đã được đưa vào chung mô hình Product phân loại bằng trường JSON thay vì các bảng riêng lẻ.")

if __name__ == "__main__":
    generate_products()
