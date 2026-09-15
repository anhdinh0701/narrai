-- =======================================================
-- NARR AI - KIỂM TRA TÀI KHOẢN & DỮ LIỆU ĐĂNG KÝ
-- Mở file này trong SQL Server Management Studio (SSMS)
-- hoặc Azure Data Studio và bấm Execute (F5)
-- =======================================================

USE NarrAIDB;
GO

-- 1. XEM TẤT CẢ TÀI KHOẢN ĐÃ ĐĂNG KÝ THÀNH CÔNG
PRINT '=======================================================';
PRINT 'DANH SÁCH TÀI KHOẢN ĐÃ ĐĂNG KÝ (BẢNG USERS):';
PRINT '=======================================================';
SELECT 
    id AS [ID],
    username AS [Tên đăng nhập],
    email AS [Email],
    name AS [Họ và tên],
    created_at AS [Ngày đăng ký],
    SUBSTRING(password_hash, 1, 15) + '... (Bcrypt)' AS [Mật khẩu đã mã hóa]
FROM users
ORDER BY id DESC;
GO

-- 2. XEM DANH SÁCH TRUYỆN ĐÃ ĐƯỢC LƯU THEO TỪNG TÀI KHOẢN
PRINT '=======================================================';
PRINT 'DANH SÁCH TRUYỆN ĐÃ LƯU CỦA NGƯỜI DÙNG (BẢNG STORIES):';
PRINT '=======================================================';
SELECT 
    s.id AS [ID Truyện],
    u.username AS [Tác giả],
    s.word_count AS [Số từ],
    s.created_at AS [Thời gian tạo],
    SUBSTRING(s.story_content, 1, 100) + '...' AS [Trích đoạn truyện]
FROM stories s
LEFT JOIN users u ON s.user_id = u.id
ORDER BY s.id DESC;
GO

-- 3. XEM DANH SÁCH KHUNG TRANH COMIC PANEL
PRINT '=======================================================';
PRINT 'DANH SÁCH KHUNG TRANH TRUYỆN TRANH (COMIC PANELS):';
PRINT '=======================================================';
SELECT 
    id AS [ID Panel],
    comic_id AS [ID Comic],
    panel_index AS [Thứ tự khung],
    layout_type AS [Bố cục],
    LEN(image_url) AS [Kích thước ảnh Base64 (Ký tự)],
    SUBSTRING(dialogue_text, 1, 60) AS [Lời thoại]
FROM comic_panels
ORDER BY id DESC;
GO

-- 4. XEM CÁC TOKEN ĐÃ ĐƯỢC THU HỒI KHI BẤM ĐĂNG XUẤT
PRINT '=======================================================';
PRINT 'DANH SÁCH TOKEN ĐÃ ĐĂNG XUẤT PHÍA SERVER (TOKEN BLACKLIST):';
PRINT '=======================================================';
SELECT 
    id AS [ID],
    jti AS [Mã định danh Token JTI],
    expires_at AS [Hạn hết hạn ban đầu]
FROM token_blacklist
ORDER BY id DESC;
GO
