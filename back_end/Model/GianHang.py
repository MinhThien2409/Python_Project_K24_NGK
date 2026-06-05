class GianHang:
    def __init__(self, StoreId=None, StoreName=None,Address=None,UserId=None):
        self.StoreId = StoreId
        self.StoreName = StoreName
        self.Address = Address
        self.UserId = UserId

    def __str__(self):
        return f"GianHang(ID={self.StoreId}, Name='{self.StoreName}', Address='{self.Address}', UserID={self.UserId})"