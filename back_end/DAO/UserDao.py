import pyodbc

import DBconnection
from Model.User import Khach,NguoiBan
class UserDao:
  def them_khach_hang(self,khach:Khach):
      conn= DBconnection.get_connection()
      if conn is None:
          return False
      cursor= conn.cursor()
      try :
          sql="""
          INSERT INTO Users (Ten_User,Dia_Chi,SDT, Vai_Tro,TenDangNhap,MatKhau
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


def kiem_tra_sdt_ton_tai(self,sdt):
        conn=DBconnection.get_connection()
        cursor=conn.cursor()
        cursor.execute("select * from Ma_User where SDT=?",(sdt,))
        row=cursor.fetchone()

        cursor.close()
        conn.close()
        return row is not None