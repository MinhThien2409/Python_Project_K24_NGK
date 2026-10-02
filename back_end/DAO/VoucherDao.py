import logging
from back_end.DBconnection import DBconnection
logger=logging.getLogger(__name__)
class VoucherDao:
    def _conn(self): return DBconnection.get_connection()
    def lay_tat_ca(self):
        c=self._conn()
        if c is None:return []
        x=c.cursor()
        try:
            x.execute("SELECT VoucherId,Code,Name,DiscountType,DiscountValue,MinOrderValue,MaxDiscount,StartDate,EndDate,Quantity,UsedQuantity,IsActive FROM Voucher ORDER BY VoucherId DESC")
            return [self._row(r) for r in x.fetchall()]
        except Exception as e:logger.exception("Loi lay voucher: %s",e);return []
        finally:x.close();c.close()
    def lay_theo_id(self,i):
        c=self._conn()
        if c is None:return None
        x=c.cursor()
        try:
            x.execute("SELECT VoucherId,Code,Name,DiscountType,DiscountValue,MinOrderValue,MaxDiscount,StartDate,EndDate,Quantity,UsedQuantity,IsActive FROM Voucher WHERE VoucherId=%s",(i,))
            r=x.fetchone();return self._row(r) if r else None
        finally:x.close();c.close()
    def lay_theo_code(self,code):
        conn=self._conn()
        if conn is None:return None
        cur=conn.cursor()
        try:
            cur.execute("SELECT VoucherId,Code,Name,DiscountType,DiscountValue,MinOrderValue,MaxDiscount,StartDate,EndDate,Quantity,UsedQuantity,IsActive FROM Voucher WHERE Code=%s",(code,))
            r=cur.fetchone();return self._row(r) if r else None
        finally:cur.close();conn.close()

    def lay_gia_san_pham(self,product_ids):
        ids=[int(x) for x in (product_ids or [])]
        if not ids:return {}
        conn=self._conn()
        if conn is None:return {}
        cur=conn.cursor()
        try:
            ph=",".join(["%s"]*len(ids))
            cur.execute(f"SELECT ProductId,Price,Quantity,IsActive FROM Products WHERE ProductId IN ({ph})",tuple(ids))
            return {int(r[0]):{"price":float(r[1] or 0),"quantity":int(r[2] or 0),"is_active":bool(r[3])} for r in cur.fetchall()}
        finally:cur.close();conn.close()

    def code_ton_tai(self,code,tru_id=None):
        c=self._conn()
        if c is None:return False
        x=c.cursor()
        try:
            q="SELECT VoucherId FROM Voucher WHERE Code=%s";a=(code,)
            if tru_id is not None:q+=" AND VoucherId<>%s";a=(code,tru_id)
            x.execute(q,a);return x.fetchone() is not None
        finally:x.close();c.close()
    def them(self,v):
        c=self._conn()
        if c is None:return False
        x=c.cursor()
        try:
            x.execute("INSERT INTO Voucher(Code,Name,DiscountType,DiscountValue,MinOrderValue,MaxDiscount,StartDate,EndDate,Quantity,UsedQuantity,IsActive) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s)",(v.Code,v.Name,v.DiscountType,v.DiscountValue,v.MinOrderValue,v.MaxDiscount,v.StartDate,v.EndDate,v.Quantity,int(bool(v.IsActive))))
            c.commit();return x.rowcount>0
        except Exception as e:c.rollback();logger.exception("Loi them voucher: %s",e);return False
        finally:x.close();c.close()
    def sua(self,v):
        c=self._conn()
        if c is None:return False
        x=c.cursor()
        try:
            x.execute("UPDATE Voucher SET Code=%s,Name=%s,DiscountType=%s,DiscountValue=%s,MinOrderValue=%s,MaxDiscount=%s,StartDate=%s,EndDate=%s,Quantity=%s,IsActive=%s WHERE VoucherId=%s",(v.Code,v.Name,v.DiscountType,v.DiscountValue,v.MinOrderValue,v.MaxDiscount,v.StartDate,v.EndDate,v.Quantity,int(bool(v.IsActive)),v.VoucherId))
            c.commit();return x.rowcount>0
        except Exception as e:c.rollback();logger.exception("Loi sua voucher: %s",e);return False
        finally:x.close();c.close()
    def toggle(self,i):
        c=self._conn()
        if c is None:return False
        x=c.cursor()
        try:x.execute("UPDATE Voucher SET IsActive=NOT IsActive WHERE VoucherId=%s",(i,));c.commit();return x.rowcount>0
        except Exception as e:c.rollback();logger.exception("Loi toggle voucher: %s",e);return False
        finally:x.close();c.close()
    def xoa(self,i):
        c=self._conn()
        if c is None:return False
        x=c.cursor()
        try:
            x.execute("SELECT UsedQuantity FROM Voucher WHERE VoucherId=%s",(i,));r=x.fetchone()
            if not r or int(r[0] or 0)>0:return False
            x.execute("DELETE FROM Voucher WHERE VoucherId=%s",(i,));c.commit();return x.rowcount>0
        except Exception as e:c.rollback();logger.exception("Loi xoa voucher: %s",e);return False
        finally:x.close();c.close()
    @staticmethod
    def _row(r):
        return {"VoucherId":r[0],"Code":r[1],"Name":r[2],"DiscountType":r[3],"DiscountValue":float(r[4]),"MinOrderValue":float(r[5] or 0),"MaxDiscount":float(r[6] or 0),"StartDate":str(r[7]) if r[7] else None,"EndDate":str(r[8]) if r[8] else None,"Quantity":int(r[9] or 0),"UsedQuantity":int(r[10] or 0),"IsActive":bool(r[11])}
