from back_end.DBconnection import DBconnection
from back_end.Model.GianHang import GianHang
class GianHangDao:
    def them_gianhang(self,gianhang:GianHang):
        conn=DBconnection().get_connection()
        if conn is None:return False
        cursor=conn.cursor()

        try:
            sql="""
            Insert into Stores( StoreName,Address,UserId)
            Values(?,?,?)
            """
            cursor.execute(sql,(

                gianhang.StoreName,
                gianhang.Address,
                gianhang.UserId

            ))
            conn.commit()
            return True
        except Exception as e:
            print("Lỗi khi thêm gian hàng",e)
            return False
        finally:
            cursor.close()
            conn.close()

    def cap_nhat_gianhang(self,gianhang:GianHang):
        conn=DBconnection().get_connection()
        if conn is None:return False
        cursor=conn.cursor()
        try:
            sql="""
            Update Stores
            set StoreName=?,Address=?,UserId=?
            Where StoreId=?
            
            """
            cursor.execute(sql,(
                gianhang.StoreName,
                gianhang.Address,
                gianhang.UserId,
                gianhang.StoreId
            ))
            conn.commit()
            return True
        except Exception as e:
            print("Lỗi khi cập nhật gian hàng",e)
            return False
        finally:
            cursor.close()
            conn.close()
    def xoa_gianhang(self,StoreId):
        conn=DBconnection().get_connection()
        if conn is None:return False
        cursor=conn.cursor()
        try :
            sql="""
            Delete from Stores  where StoreId=?
            """ 

            cursor.execute(sql,(StoreId,))
            conn.commit()
            return cursor.rowcount>0
        except Exception as e:
            print("Lỗi khi xoá Gian Hàng",e)
            return False
        finally:
            cursor.close()
            conn.close()
