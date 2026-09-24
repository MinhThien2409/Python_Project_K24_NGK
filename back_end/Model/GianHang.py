class GianHang:
    """Gian hang cua seller, lien ket 1-1 voi Users qua UserId."""
    def __init__(self, StoreId=None, StoreName=None, Address=None,
                 UserId=None, Phone=None, Category=None,
                  Description=None, ThamNien=None, IsActive=1):
        """Khởi tạo gian hàng của người bán với thông tin liên hệ."""
        self.StoreId     = StoreId
        self.StoreName   = StoreName
        self.Address     = Address
        self.UserId      = UserId
        self.Phone       = Phone
        self.Category    = Category
        self.Description = Description
        self.ThamNien    = ThamNien
        self.IsActive    = IsActive

    def __str__(self):
        """Trả về chuỗi mô tả ngắn gọn của gian hàng."""
        return (f"GianHang(ID={self.StoreId}, Name='{self.StoreName}', "
                f"Address='{self.Address}', UserID={self.UserId})")