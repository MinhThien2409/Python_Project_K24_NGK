import pyodbc

from DBconnection import DBconnection
from Model.User import Khach,NguoiBan
class UserDao:
  def them_khach_hang(self,khach:Khach):
      conn= DBconnection.get_connection()
      if conn is None:
          return False
      cursor= conn.cursor()
      try :
          sql="""
          INSERT INTO Users (Ten_User,Dia_Chi,SDT, Vai_Tro,TenDangNhap,MatKhau)
          VALUES(?,?,?,?,?,?)
          """
          cursor.execute(sql,(khach.ten_user,khach.dia_chi,khach.sdt,khach.vai_tro,khach.tendangnhap,khach.mat_khau))
          conn.commit()
          return True
      except Exception as e :
          print("Lỗi khi thêm khách hàng",e)
          return False
      finally:
          cursor.close()
          conn.close()

  def kiem_tra_tendangnhap_ton_tai(self,tendangnhap):
            conn=DBconnection.get_connection()
            if conn is None:
                return False

            cursor=conn.cursor()
            cursor.execute("select  Ma_User FROM Users where TenDangNhap=?",(tendangnhap,))
            row=cursor.fetchone()

            cursor.close()
            conn.close()
            return row is not None
  def lay_danh_sach_user(self):
      conn=DBconnection.get_connection()
      if conn is None:
          return []
      cursor=conn.cursor()
      try:
          sql="""
          SELECT Ma_User,Ma_Khach_Hang,Ten_User,Dia_Chi,SDT,Vai_Tro,TenDangNhap From Users
          """
          cursor.execute(sql)
          rows =cursor.fetchall()

          danh_sach_user=[]
          for row in rows:
              user={
                  "ma_user":row.Ma_User,
                  "ma_khach_hang":row.Ma_Khach_Hang,
                  "ten_user":row.Ten_User,
                  "dia_chi":row.Dia_Chi,
                  "sdt":row.SDT,
                  "vai_tro":row.Vai_Tro,
                  "tendangnhap":row.TenDangNhap,

              }
              danh_sach_user.append(user)
          return danh_sach_user
      except Exception as e :
          print("Lỗi khi lấy danh sách User :",e)
          return []
      finally:
          cursor.close()
          conn.close()

  def cap_nhat_user(self,ma_user,ten_user,dia_chi,sdt):
        conn=DBconnection.get_connection()
        if conn is None:
            return False
        cursor=conn.cursor()
        try:
            sql="""
            UPDATE Users
            set Ten_User=?,Dia_Chi=?,SDT=?
            WHERE Ma_User=?
            """
            cursor.execute(sql,(ten_user,dia_chi,sdt,ma_user))
            conn.commit()
            if cursor.rowcount > 0:
                return True
            return False
        except Exception as e :
            print("Lỗi khi cập nhất User:",e)
            return False
        finally:
            cursor.close()
            conn.close()
  def xoa_user(self,ma_user):
      conn=DBconnection.get_connection()
      if conn is None:
          return False
      cursor=conn.cursor()
      try:
          sql="""
          DELETE FROM Users where Ma_User=?"""
          cursor.execute(sql,(ma_user,))
          conn.commit()
          if(cursor.rowcount > 0):
              return True
          return False
      except Exception as e :
          print("Lỗi khi xoá User:",e)
          return False
      finally:
          cursor.close()
          conn.close()
