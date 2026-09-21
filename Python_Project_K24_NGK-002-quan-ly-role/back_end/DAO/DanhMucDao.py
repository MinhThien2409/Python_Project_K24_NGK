import logging

from back_end.DBconnection import DBconnection
from back_end.Model.DanhMuc import DanhMuc

logger = logging.getLogger(__name__)


class DanhMucDao:

    # ─── ĐỌC ───

    def lay_tat_ca(self):
        """Lấy toàn bộ danh mục sắp xếp theo CategoryId."""
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT CategoryId, CategoryName FROM Categories ORDER BY CategoryId")
            rows = cursor.fetchall()
            return [{"id": r.CategoryId, "name": r.CategoryName} for r in rows]
        except Exception as e:
            logger.exception("Lỗi lay_tat_ca categories: %s", e)
            return []
        finally:
            cursor.close(); conn.close()

    def kiem_tra_ten_ton_tai(self, ten, tru_id=None):
        """Kiểm tra tên danh mục đã tồn tại chưa (không phân biệt hoa/thường)."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            if tru_id is None:
                cursor.execute(
                    "SELECT CategoryId FROM Categories "
                    "WHERE LOWER(LTRIM(RTRIM(CategoryName))) = LOWER(LTRIM(RTRIM(?)))",
                    (ten,)
                )
            else:
                cursor.execute(
                    "SELECT CategoryId FROM Categories "
                    "WHERE LOWER(LTRIM(RTRIM(CategoryName))) = LOWER(LTRIM(RTRIM(?))) "
                    "AND CategoryId <> ?",
                    (ten, tru_id)
                )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.exception("Lỗi kiem_tra_ten_ton_tai: %s", e)
            return False
        finally:
            cursor.close(); conn.close()

    def dem_san_pham(self, category_id):
        """Đếm số sản phẩm thuộc danh mục (FR-003)."""
        conn = DBconnection.get_connection()
        if conn is None: return None
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM Products WHERE CategoryId=?",
                (category_id,)
            )
            return cursor.fetchone()[0]
        except Exception as e:
            logger.exception("Lỗi dem_san_pham: %s", e)
            return None
        finally:
            cursor.close(); conn.close()

    # ─── GHI ───

    def them(self, category: DanhMuc):
        """Thêm danh mục mới vào bảng Categories."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Categories (CategoryName) VALUES (?)",
                (category.CategoryName,)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.exception("Lỗi them category: %s", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()

    def sua(self, category: DanhMuc):
        """Cập nhật tên danh mục theo CategoryId."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE Categories SET CategoryName=? WHERE CategoryId=?",
                (category.CategoryName, category.CategoryId)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi sua category: %s", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()

    def xoa(self, category_id):
        """Xóa danh mục theo CategoryId."""
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM Categories WHERE CategoryId=?",
                (category_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception("Lỗi xoa category: %s", e)
            conn.rollback()
            return False
        finally:
            cursor.close(); conn.close()
