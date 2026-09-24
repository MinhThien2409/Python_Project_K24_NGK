import logging

from back_end.DBconnection import DBconnection
from back_end.Model.DanhMuc import DanhMuc

logger = logging.getLogger(__name__)


class DanhMucDao:

    # ─── ĐỌC ───

    def lay_tat_ca(self):
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT c.CategoryId, c.CategoryName,
                       COALESCE(c.PlatformFeePercent, 0) AS PlatformFeePercent,
                       COUNT(p.ProductId) AS SoSanPham
                FROM categories c
                LEFT JOIN products p ON c.CategoryId = p.CategoryId AND p.IsActive = 1
                GROUP BY c.CategoryId, c.CategoryName, c.PlatformFeePercent
                ORDER BY c.CategoryId
            """)
            rows = cursor.fetchall()
            return [
                {
                    "category_id": r.CategoryId,
                    "category_name": r.CategoryName,
                    "platform_fee_percent": float(r.PlatformFeePercent),
                    "so_san_pham": r.SoSanPham
                } for r in rows
            ]
        except Exception as e:
            print("Lỗi lay_tat_ca DanhMuc:", e)
            return []
        finally:
            cursor.close();
            conn.close()

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

    def them(self, dm: DanhMuc):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO categories (CategoryName, PlatformFeePercent) VALUES (?, ?)",
                (dm.CategoryName, dm.PlatformFeePercent or 0)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi them DanhMuc:", e)
            return False
        finally:
            cursor.close();
            conn.close()

    def sua(self, dm: DanhMuc):
        conn = DBconnection.get_connection()
        if conn is None: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE categories SET CategoryName=?, PlatformFeePercent=? WHERE CategoryId=?",
                (dm.CategoryName, dm.PlatformFeePercent or 0, dm.CategoryId)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print("Lỗi sua DanhMuc:", e)
            return False
        finally:
            cursor.close();
            conn.close()

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
