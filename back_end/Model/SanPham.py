class SanPham:
    def __init__(
        self,
        ProductId    = None,
        ProductName  = None,
        Description  = None,
        Price        = None,
        OldPrice     = None,
        Quantity     = None,
        SoldCount    = 0,
        Emoji        = None,
        ImageUrl = None,
        CategoryId   = None,
        StoreId      = None,
        IsActive     = 1
    ):
        """Khởi tạo sản phẩm với thông tin giá, tồn kho và phân loại."""
        self.ProductId   = ProductId
        self.ProductName = ProductName
        self.Description = Description
        self.Price       = Price
        self.OldPrice    = OldPrice
        self.Quantity    = Quantity
        self.SoldCount   = SoldCount
        self.Emoji       = Emoji
        self.ImageUrl = ImageUrl
        self.CategoryId  = CategoryId
        self.StoreId     = StoreId
        self.IsActive    = IsActive