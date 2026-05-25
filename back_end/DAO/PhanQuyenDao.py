from DBconnection import DBconnection
class PhanQuyenDao:
    def dong_bo_quyen_xuong_user(self,ma_nhom,ma_chuc_nang,xem,them,sua,xoa):
        conn=DBconnection.get_connection()
        if(conn is  None):
            return False
        cursor=conn.cursor()
        try:
            cursor.execute("Select Ma_User From Users Where Ma_Nhom_Quyen=? ",(ma_nhom,))
            user = cursor.fetchall()
            for u in user:
                ma_user=u.Ma_User
                cursor.execute("Select is_custom From Phan_Quyen where Ma_User=? And Ma_Chuc_Nang=?",(ma_user,ma_chuc_nang))
                row=cursor.fetchone()

                if row:
                    if not row.is_custom:
                        sql_update="""
                        Update Phan_Quyen
                        Set Duoc_Xem=?,Duoc_Them=?,Duoc_Sua=?,Duoc_Xoa=?
                        Where Ma_User=? And Ma_Chuc_Nang=? And is_custom=0
                        """
                        cursor.execute(sql_update,(xem,them,sua,xoa,ma_user,ma_chuc_nang))
                    else:
                        sql_insert="""
                        Insert into Phan_Quyen(Ma_User,Ma_Chuc_Nang,Duoc_Xem,Duoc_Them,Duoc_Sua,Duoc_Xoa,is_custom)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                        """
                        cursor.execute(sql_insert,(ma_user,ma_chuc_nang,xem,them,sua,xoa))
                        conn.commit()
                        return True
        except Exception as e:
            print("Lỗi đồng bộ quyền ",e)
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()
    def cap_quyen_ngoai_le_user(self,ma_user,ma_chuc_nang,xem,them,sua,xoa):
        conn=DBconnection.get_connection()
        if(conn is None):
            return False
        cursor=conn.cursor()
        try:
            sql="""
            Update Phan_Quyen
            Set Duoc_Xem=?,
            Set Duoc_Them=?,
            Set Duoc_Sua=?,
            Set Duoc_Xoa=?,
            is_custom=1
            Where Ma_User=? And Ma_Chuc_Nang=?
            """
            cursor.execute(sql,(xem,them,sua,xoa,ma_user,ma_chuc_nang))
            conn.commit()
            return True
        except Exception as e:
            print("Lỗi cấp ngoại lệ",e)
            return False
        finally:
            cursor.close()
            conn.close()
    def khoi_phuc_ve_quyen_nhom(self,ma_user,ma_chuc_nang,xem_nhom, them_nhom, sua_nhom, xoa_nhom):
        conn=DBconnection.get_connection()
        if(conn is None):
            return False
        cursor=conn.cursor()
        try:
            sql="""
            Update Phan_Quyen
            Set Duoc_Xem=?,Duoc_Them=?,Duoc_Sua=?,Duoc_Xoa=?,is_custom=0
            Where Ma_User=? And Ma_Chuc_Nang=?
            """
            cursor.execute(sql,(xem_nhom,them_nhom,sua_nhom,xoa_nhom,ma_user,ma_chuc_nang))
            conn.commit()
            return True
        except Exception as e:
            print("Lỗi khôi phục quyền",e)
            return False
        finally:
            cursor.close()
            conn.close()


