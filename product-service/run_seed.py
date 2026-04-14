import os, random, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from modules.catalog.infrastructure.models.product_model import ProductModel
from modules.catalog.infrastructure.models.category_model import CategoryModel
from modules.catalog.infrastructure.models.brand_model import BrandModel
from modules.catalog.infrastructure.models.product_type_model import ProductTypeModel


def vnd_price(low, high):
    return random.randrange(int(low), int(high) + 1000, 1000)

ProductModel.objects.all().delete()
CategoryModel.objects.all().delete()
BrandModel.objects.all().delete()
ProductTypeModel.objects.all().delete()

type_book, _ = ProductTypeModel.objects.get_or_create(name='Book')
type_clothes, _ = ProductTypeModel.objects.get_or_create(name='Clothes')
type_generic, _ = ProductTypeModel.objects.get_or_create(name='Generic')

data = [
    ("Sach Khoa hoc", type_book, [
        {"brand": "NXB Tre", "items": ["Vu tru hoc co ban", "Sapiens Luoc su loai nguoi", "Tu dien Y hoc", "Sinh hoc dai cuong", "Vat ly luong tu"], "attr": {"author": "Nhieu tac gia", "pages": 300}, "img": "https://m.media-amazon.com/images/I/51h5d4dYaoL._SX258_BO1,204,203,200_.jpg"},
    ]),
    ("Sach Lap trinh", type_book, [
        {"brand": "OReilly", "items": ["Clean Code", "Design Pattern", "Mastering Python", "Docker Deep Dive", "Kubernetes in Action"], "attr": {"author": "IT Expert", "isbn": "978-0123456"}, "img": "https://m.media-amazon.com/images/I/5131OWtQRaL._SX381_BO1,204,203,200_.jpg"},
    ]),
    ("Thoi trang Nam", type_clothes, [
        {"brand": "Uniqlo", "items": ["Ao khoac gio", "Ao thun co ban", "Quan Jeans Slim-fit", "Ao so mi dai tay", "Ao len co lo"], "attr": {"size": "L", "color": "Navy", "material": "Cotton"}, "img": "https://image.uniqlo.com/UQ/ST3/WesternCommon/imagesgoods/462666/item/goods_69_462666.jpg"},
    ]),
    ("Thoi trang The thao", type_clothes, [
        {"brand": "Nike", "items": ["Ao chay bo Dri-Fit", "Quan dui chay", "Bo the thao thu dong", "Ao tank top gym", "Ao khoac chong gio"], "attr": {"size": "XL", "color": "Trang", "technology": "Dri-fit"}, "img": "https://static.nike.com/a/images/c_limit,w_592,f_auto/t_product_v1/e1c72b15-4f3e-4a53-8bf0-4be6a8d1e6d0/sportswear.jpg"},
    ]),
    ("Dien thoai thong minh", type_generic, [
        {"brand": "Apple", "items": ["iPhone 15 Pro Max", "iPhone 15", "iPhone 14 Plus", "iPhone SE 3", "iPhone 15 Pro"], "attr": {"ram": "8GB", "storage": "256GB", "screen": "OLED 6.7"}, "img": "https://store.storeimages.cdn-apple.com/8756/as-images.apple.com/is/iphone-15-pro-finish-select-202309-6-7inch-naturaltitanium"},
        {"brand": "Samsung", "items": ["Galaxy S24 Ultra", "Galaxy S23", "Galaxy Z Fold 5", "Galaxy Z Flip 5", "Galaxy A54"], "attr": {"ram": "12GB", "storage": "512GB", "battery": "5000mAh"}, "img": "https://images.samsung.com/is/image/samsung/p6pim/vn/2401/gallery/vn-galaxy-s24-s928"},
    ]),
    ("May tinh xach tay", type_generic, [
        {"brand": "Dell", "items": ["XPS 15 9530", "XPS 13 Plus", "Inspiron 16", "Alienware x17", "G15 Gaming"], "attr": {"cpu": "Intel i7 13th", "ram": "16GB", "ssd": "1TB"}, "img": "https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/xps-notebooks/15-9530/media-gallery/silver/notebook-xps-15-9530.psd"},
        {"brand": "Apple", "items": ["MacBook Pro 16 M3 Max", "MacBook Air M2", "MacBook Pro 14 M3", "MacBook Air M1", "Mac mini M2"], "attr": {"cpu": "Apple M-Series", "ram": "16GB", "storage": "512GB"}, "img": "https://store.storeimages.cdn-apple.com/8756/as-images.apple.com/is/mbp14-spacegray-select-202310"},
    ]),
    ("My pham", type_generic, [
        {"brand": "LOreal", "items": ["Kem chong nang UV", "Tay trang Micellar", "Kem duong cap am", "Son thoi do cam", "Serum Vitamin C"], "attr": {"volume": "50ml", "skin_type": "Moi loai da", "origin": "Phap"}, "img": "https://www.loreal-paris.de/-/media/project/loreal/brand-sites/oap/emea/de/products/skin-care/revitalift/revitalift-filler-eye-cream/revitalift-filler.png"},
    ]),
    ("Noi that", type_generic, [
        {"brand": "IKEA", "items": ["Ban lam viec LINNMON", "Ghe xoay MARKUS", "Tu quan ao PAX", "Giuong doi MALM", "Ke sach BILLY"], "attr": {"material": "Go cong nghiep", "color": "Trang/Den", "assembly_needed": "Yes"}, "img": "https://www.ikea.com/global/assets/navigation/images/desks-computer-desks-20649.jpeg"},
    ]),
    ("May anh", type_generic, [
        {"brand": "Sony", "items": ["Alpha a7 IV", "Alpha a6700", "ZV-E10 Vlog", "FX3 Cinema", "Cyber-shot RX100"], "attr": {"sensor": "Full-frame", "megapixels": "33MP", "lens_mount": "Sony E"}, "img": "https://www.bhphotovideo.com/images/images2500x2500/sony_ilce_7m4_b_alpha_a7_iv.jpg"},
    ]),
    ("Do choi", type_generic, [
        {"brand": "LEGO", "items": ["Millennium Falcon", "Porsche 911 GT3", "Lau dai Hogwarts", "Lego City Police", "Thap Eiffel"], "attr": {"pieces": 1500, "age_rating": "12+", "material": "Nhua ABS"}, "img": "https://www.lego.com/cdn/cs/set/assets/blt1f2d26d57cc178d8/75192.jpg"},
    ]),
    ("Van phong pham", type_generic, [
        {"brand": "Moleskine", "items": ["So tay Classic A5", "So Bullet Journal", "So phac thao Art", "But bi Moleskine", "Binder clip set"], "attr": {"paper_type": "Blank/Lined", "pages": 240, "cover": "Hardcover"}, "img": "https://images-na.ssl-images-amazon.com/images/I/61FKpnUBY4L._SX679_.jpg"},
    ]),
    ("Trang suc", type_generic, [
        {"brand": "Swarovski", "items": ["Day chuyen Thien nga", "Khuyen tai Iconic", "Lac tay pha le", "Nhan kim cuong", "Vong co anh sao"], "attr": {"material": "Bac/Pha le", "color": "Bach kim", "gem": "Crystal"}, "img": "https://www.swarovski.com/on/demandware.static/-/Sites-swarovski-master-catalog/default/dweabf7ad6/images/swa/5007735.jpg"},
    ]),
    ("Do the thao", type_generic, [
        {"brand": "Nike", "items": ["Giay chay Pegasus 40", "Giay bong ro LeBron 20", "Tui trong the thao", "Bong da Premier", "Balo Nike Air"], "attr": {"sport": "Chay bo / Da nang", "size": "US 9"}, "img": "https://static.nike.com/a/images/c_limit,w_592,f_auto/t_product_v1/a0d1gxc7tmtuudwq9xks/pegasus-40.png"},
    ]),
    ("Do cho thu cung", type_generic, [
        {"brand": "Royal Canin", "items": ["Thuc an hat cho Meo", "Thuc an hat Poodle", "Pate meo con", "Thuc an kieng cho lon", "Snack cho meo"], "attr": {"weight": "2kg", "flavor": "Meat", "pet_type": "Meo/Cho"}, "img": "https://www.royalcanin.com/cdn/royal-canin/product-image/medium-adult.png"},
    ]),
    ("Nhac cu", type_generic, [
        {"brand": "Yamaha", "items": ["Piano Dien P-45", "Guitar Classic C40", "Acoustic F310", "Sao dien tu Venova", "Organ PSR-E473"], "attr": {"instrument_type": "Phim / Day", "color": "Go / Den"}, "img": "https://vn.yamaha.com/vi/products/contents/keyboards/p_series/images/p-45_b_01.jpg"},
    ]),
    ("Cong cu xay dung", type_generic, [
        {"brand": "Bosch", "items": ["May khoan dong luc", "May mai goc GWS", "Bo van vit 32 mon", "May cua long GST", "May rua xe cao ap"], "attr": {"power": "600W", "cordless": "No", "warranty": "1 Year"}, "img": "https://www.bosch-pt.com.vn/vn/media/ptng_images/product_images/gsb_16_re.jpg"},
    ]),
    ("Thuc pham", type_generic, [
        {"brand": "Oreo", "items": ["Banh quy Oreo Vani", "Oreo Dau tay", "Oreo Socola", "Oreo Matcha", "Banh xop Oreo"], "attr": {"weight": "137g", "flavor": "Sweet", "diet": "Normal"}, "img": "https://product.hstatic.net/200000305145/product/oreo-vani-137g.jpg"},
    ]),
]

total = 0
for cat_name, ptype, groups in data:
    cat, _ = CategoryModel.objects.get_or_create(name=cat_name, defaults={"description": cat_name})
    for g in groups:
        brand, _ = BrandModel.objects.get_or_create(name=g["brand"])
        for item_name in g["items"]:
            for sfx in ["", " Pro", " Plus", " Lite"]:
                price = vnd_price(120000, 3500000)
                if "iPhone" in item_name or "MacBook" in item_name or "XPS" in item_name:
                    price = vnd_price(3000000, 35000000)
                if "Oreo" in item_name or "But" in item_name:
                    price = vnd_price(10000, 300000)
                ProductModel.objects.create(
                    name=item_name + sfx,
                    description="San pham " + item_name + sfx + " chinh hang tu " + g["brand"] + ". " + cat_name + " chat luong cao.",
                    price=price,
                    stock=random.randint(5, 150),
                    image_url=g["img"],
                    category=cat,
                    brand=brand,
                    product_type=ptype,
                    attributes=g["attr"],
                )
                total += 1

print("Created " + str(total) + " products in " + str(len(data)) + " categories")
