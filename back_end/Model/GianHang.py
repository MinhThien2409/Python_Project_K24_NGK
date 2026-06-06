class GianHang:
    def __init__(self, StoreId=None, StoreName=None, Address=None,
                 UserId=None, Phone=None, Category=None,
                 Description=None, IsActive=1):
        self.StoreId     = StoreId
        self.StoreName   = StoreName
        self.Address     = Address
        self.UserId      = UserId
        self.Phone       = Phone
        self.Category    = Category
        self.Description = Description
        self.IsActive    = IsActive

    def __str__(self):
        return (f"GianHang(ID={self.StoreId}, Name='{self.StoreName}', "
                f"Address='{self.Address}', UserID={self.UserId})")