# Bảng Mô Tả Các Use Case - Hệ Thống Bán Sách và Sản Phẩm Điện Tử Microservices

## **NHÓM CUSTOMER** (11 Use Cases)

| Mã UC | Tên Usecase | Actor | Tiền Điều Kiện | Luồng Sự Kiện Chính |
|-------|-----------|-------|-----------------|-------------------|
| UC-01 | Đăng ký tài khoản | Customer | Chưa có tài khoản | 1. Nhập email, mật khẩu, họ tên. 2. Xác thực email (nếu có). 3. Tạo tài khoản trong auth-service. 4. Lưu vào DB. 5. Hiển thị thành công. |
| UC-02 | Đăng nhập / Đăng xuất | Customer | Có tài khoản, chưa đăng nhập | 1. Nhập email/mật khẩu. 2. Gọi auth-service xác thực. 3. Cấp JWT access token + refresh token. 4. Lưu session frontend. 5. Chuyển hướng đến trang chính. **Đăng xuất:** 1. Xóa token trong localStorage. 2. Xóa session. 3. Chuyển hướng login. |
| UC-03 | Xem danh sách sản phẩm | Customer | Đã truy cập store | 1. Gọi product-service lấy danh sách products. 2. Hiển thị sản phẩm dưới dạng grid/list. 3. Hỗ trợ phân trang (pagination). 4. Có thể lọc theo category/brand. |
| UC-04 | Tìm kiếm / lọc sản phẩm | Customer | Đã xem danh sách | 1. Nhập từ khóa tìm kiếm. 2. Chọn bộ lọc (category, price range, brand). 3. Gọi product-service với query parameters. 4. Hiển thị kết quả filtered. 5. Hỗ trợ sắp xếp (sort by price, rating, date). |
| UC-05 | Xem chi tiết sản phẩm | Customer | Đã chọn một sản phẩm | 1. Gọi product-service lấy product detail. 2. Hiển thị hình ảnh, giá, mô tả, attributes. 3. Hiển thị danh sách reviews công khai. 4. Nút "Thêm vào giỏ" & "Đánh giá" (nếu logged in). |
| UC-06 | Quản lý giỏ hàng | Customer | Đã đăng nhập | **Thêm sản phẩm:** 1. Chọn quantity. 2. Gọi cart-service POST /cart-items/. 3. Cập nhật UI. **Cập nhật số lượng:** 1. Chỉnh quantity. 2. Gọi PATCH /cart-items/{id}/. **Xóa sản phẩm:** 1. Nhấn delete. 2. Gọi DELETE /cart-items/{id}/. |
| UC-07 | Checkout / Đặt hàng | Customer | Đã đăng nhập, giỏ hàng có sản phẩm | 1. Xem tóm tắt giỏ & tổng tiền. 2. Nhập thông tin nhận hàng (tên, phone, address). 3. Chọn phương thức thanh toán (COD / Bank Transfer). 4. Gọi order-service tạo Order. 5. Nếu Bank Transfer: Chuyển sang UC-09. Nếu COD: Tạo Payment + Shipment request. 6. Xóa giỏ hàng. 7. Chuyển hướng UC-08. |
| UC-08 | Xem lịch sử đơn hàng | Customer | Đã đăng nhập | 1. Gọi order-service lấy orders của customer. 2. Hiển thị danh sách orders với status (pending, confirmed, shipped, delivered). 3. Có thể click vào một order để xem chi tiết items + tracking. 4. Nếu status=shipped: cho phép nhấn "Đã nhận hàng" để cập nhật sang delivered. |
| UC-09 | Xác nhận thanh toán chuyển khoản | Customer | Đã chọn Bank Transfer trong Checkout | 1. Hiển thị thông tin chuyển khoản (STK, số tiền, ghi chú). 2. Customer chuyển khoản ngoài hệ thống. 3. Quay lại hệ thống chọn "Đã chuyển khoản". 4. Gọi pay-service cập nhật Payment status → completed. 5. Tạo Shipment request. 6. Cập nhật Order status. 7. Hiển thị confirmation. |
| UC-10 | Đánh giá / bình luận sản phẩm | Customer | Đã mua sản phẩm (có trong order history) | 1. Từ UC-05 hoặc UC-08, nhấn "Đánh giá". 2. Chọn số sao (1-5). 3. Viết bình luận (optional). 4. Gọi comment-rate-service POST /reviews/. 5. Hiển thị review công khai. 6. Có thể xem tất cả reviews của sản phẩm. |
| UC-11 | Tư vấn sản phẩm bằng AI | Customer | Đã đăng nhập (optional) | 1. Nhấn "AI Tư vấn" trong nav. 2. Nhập câu hỏi về sản phẩm. 3. AI Advisor (RAG + behavior KB) phân tích & gợi ý. 4. Hiển thị kết quả + danh sách sản phẩm đề xuất. 5. Có thể thêm vào giỏ trực tiếp. 6. Lưu lịch tương tác cho behavior analysis. |

---

## **NHÓM ADMIN** (5 Use Cases)

| Mã UC | Tên Usecase | Actor | Tiền Điều Kiện | Luồng Sự Kiện Chính |
|-------|-----------|-------|-----------------|-------------------|
| UC-12 | Quản lý sản phẩm | Admin | Đã xác thực Role=Admin | **Xem danh sách:** 1. Gọi product-service lấy products. 2. Hiển thị bảng với columns: ID, Name, Type, Category, Price, Stock. 3. Hỗ trợ tìm kiếm & phân trang. **Thêm mới:** 1. Form: name, description, price, stock, image_url, category, brand, product_type, attributes. 2. POST /products/. 3. Cập nhật DB. **Sửa:** 1. PATCH /products/{id}/ với thông tin mới. **Xóa:** 1. DELETE /products/{id}/ (soft-delete hoặc hard-delete). |
| UC-13 | Quản lý danh mục | Admin | Đã xác thực Role=Admin | **Xem danh sách:** 1. Gọi product-service lấy categories. **Thêm danh mục:** 1. Form: category_name, description. 2. POST /categories/. **Sửa danh mục:** 1. PATCH /categories/{id}/. **Xóa danh mục:** 1. DELETE /categories/{id}/ (kiểm tra nếu có products liên quan). |
| UC-14 | Quản lý thương hiệu | Admin | Đã xác thực Role=Admin | **Xem danh sách:** 1. Gọi product-service lấy brands. **Thêm thương hiệu:** 1. Form: brand_name, description, logo_url. 2. POST /brands/. **Sửa thương hiệu:** 1. PATCH /brands/{id}/. **Xóa thương hiệu:** 1. DELETE /brands/{id}/ (kiểm tra products liên quan). |
| UC-15 | Quản lý loại sản phẩm | Admin | Đã xác thực Role=Admin | **Xem danh sách:** 1. Gọi product-service lấy product_types (Book, Clothes, Generic). 2. Hiển thị attributes schema cho mỗi type. **Cập nhật loại:** 1. Chỉnh sửa attributes JSON schema. 2. PATCH /product-types/{id}/. 3. Cập nhật trên tất cả products có type đó (nếu cần). |
| UC-16 | Quản lý tài khoản nhân sự | Admin | Đã xác thực Role=Admin | **Xem danh sách:** 1. Gọi auth-service lấy users. 2. Hiển thị email, full_name, role (Admin/Staff/Manager), is_active. **Tạo tài khoản:** 1. Form: email, password, full_name, role. 2. POST /auth/register/ với role được chỉ định. 3. Tạo trong auth-service. **Cập nhật role:** 1. PATCH /users/{id}/ thay đổi role. **Kích hoạt/Vô hiệu hóa:** 1. PATCH /users/{id}/ thay đổi is_active. |

---

## **NHÓM STAFF** (3 Use Cases)

| Mã UC | Tên Usecase | Actor | Tiền Điều Kiện | Luồng Sự Kiện Chính |
|-------|-----------|-------|-----------------|-------------------|
| UC-17 | Xử lý giao hàng | Staff | Đã xác thực Role=Staff | 1. Xem danh sách Order có status=confirmed & payment_status=completed. 2. Chọn một order. 3. Tạo Shipment: POST /shipments/ với order_id, carrier, estimated_delivery. 4. Cập nhật Order status → shipped. 5. Cập nhật Shipment status → processing. 6. Lưu thông tin tracking. 7. Gửi notification tới customer. |
| UC-18 | Cập nhật trạng thái vận chuyển | Staff | Đã tạo Shipment | 1. Xem danh sách Shipment cần update. 2. Chọn Shipment. 3. Cập nhật tracking status (processing → shipped → out_for_delivery → delivered). 4. PATCH /shipments/{id}/ với status mới & tracking_info. 5. Nếu status=delivered: Cập nhật Order status → delivered. 6. Gửi notification cho customer. |
| UC-19 | Xem các đơn hàng cần giao | Staff | Đã xác thực Role=Staff | 1. Gọi order-service lấy orders có status=confirmed & payment_status=completed. 2. Hiển thị danh sách orders (ID, customer, receiver, address, created_at). 3. Sắp xếp theo ngày tạo (mới nhất trước). 4. Có thể filter theo địa chỉ / carrier. 5. Nhấn vào order để xem chi tiết và xử lý UC-17. |

---

## **NHÓM MANAGER** (2 Use Cases)

| Mã UC | Tên Usecase | Actor | Tiền Điều Kiện | Luồng Sự Kiện Chính |
|-------|-----------|-------|-----------------|-------------------|
| UC-20 | Xem dashboard / thống kê kinh doanh | Manager | Đã xác thực Role=Manager | 1. Gọi order-service, pay-service, ship-service để lấy dữ liệu. 2. Hiển thị dashboard với widgets: - Total Orders (hôm nay, tuần, tháng). - Total Revenue (tính từ Payment records). - Order Status Distribution (pie chart). - Recent Orders (table). - Top Products by Sales. - Payment Methods Distribution. 3. Hỗ trợ filter by date range. |
| UC-21 | Theo dõi tình trạng đơn hàng, thanh toán, giao hàng | Manager | Đã xác thực Role=Manager | 1. Gọi order-service lấy tất cả orders với statuses. 2. Gọi pay-service lấy payment records + statuses. 3. Gọi ship-service lấy shipment records + tracking. 4. Hiển thị unified view: Order ID → Payment Status → Shipment Status. 5. Có thể search by Order ID / Customer ID. 6. Có bộ lọc: date range, payment method, shipment status, order status. 7. Export report (CSV/PDF nếu cần). |

---

## **Các Quan Hệ Include/Extend**

### Trong Checkout (UC-07):
- **UC-07 <<include>> Create Order** (bắt buộc)
- **UC-07 <<include>> Create Payment** (bắt buộc)
- **UC-07 <<include>> Create Shipment Request** (bắt buộc)

### Quản lý Giỏ Hàng (UC-06):
- **UC-06 <<include>> Add Item to Cart**
- **UC-06 <<include>> Update Item Quantity**
- **UC-06 <<include>> Remove Item from Cart**

### Đánh Giá Sản Phẩm (UC-10):
- **UC-05 <<extend>> UC-10** (Khi xem chi tiết, customer có thể chọn đánh giá)
- **UC-08 <<extend>> UC-10** (Khi xem đơn hàng, customer có thể đánh giá sản phẩm đã mua)

### Tư Vấn AI (UC-11):
- **UC-03 <<extend>> UC-11** (Khi xem danh sách, customer có thể chat với AI)
- **UC-04 <<extend>> UC-11** (Khi tìm kiếm, customer có thể dùng AI để tìm)

### Xử Lý Giao Hàng (UC-17):
- **UC-17 <<include>> UC-18** (Cập nhật tracking là bắt buộc)

### Quản Lý Sản Phẩm (UC-12):
- **UC-12 <<include>> CRUD Operations** (Thêm, Sửa, Xóa, Xem)

---

## **Tóm Tắt**

| Nhóm | Số UC | Mô Tả |
|-----|-------|-------|
| Customer | 11 | Các chức năng mua sắm, đánh giá, tư vấn AI |
| Admin | 5 | Quản lý sản phẩm, danh mục, thương hiệu, loại sản phẩm, tài khoản |
| Staff | 3 | Xử lý vận chuyển, cập nhật tracking |
| Manager | 2 | Thống kê kinh doanh, theo dõi trạng thái đơn hàng |
| **TỔNG** | **21** | **Hệ thống đầy đủ cho microservices bookstore** |

