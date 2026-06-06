from back_end.DBconnection import DBconnection
from back_end.Model.DanhMuc import DanhMuc

class DanhMucDao:

    def lay_tat_ca(self):
        conn = DBconnection.get_connection()
        if conn is None: return []
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT CategoryId, CategoryName FROM Categories ORDER BY CategoryId")
            rows = cursor.fetchall()
            return [{"id": r.CategoryId, "name": r.CategoryName} for r in rows]
        except Exception as e:
            print("Lỗi lay_tat_ca categories:", e)
            return []
        finally:
            cursor.close(); conn.close()

    def them(self, category: DanhMuc):
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
            print("Lỗi them category:", e)
            return False
        finally:
            cursor.close(); conn.close()

    def sua(self, category: DanhMuc):
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
            print("Lỗi sua category:", e)
            return False
        finally:
            cursor.close(); conn.close()

    def xoa(self, category_id):
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
            print("Lỗi xoa category:", e)
            return False
        finally:
            cursor.close(); conn.close()