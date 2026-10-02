class Voucher:
    def __init__(self, VoucherId=None, Code=None, Name=None, DiscountType=None, DiscountValue=0, MinOrderValue=0, MaxDiscount=0, StartDate=None, EndDate=None, Quantity=0, UsedQuantity=0, IsActive=True):
        self.VoucherId=VoucherId; self.Code=Code; self.Name=Name; self.DiscountType=DiscountType; self.DiscountValue=DiscountValue; self.MinOrderValue=MinOrderValue; self.MaxDiscount=MaxDiscount; self.StartDate=StartDate; self.EndDate=EndDate; self.Quantity=Quantity; self.UsedQuantity=UsedQuantity; self.IsActive=IsActive
