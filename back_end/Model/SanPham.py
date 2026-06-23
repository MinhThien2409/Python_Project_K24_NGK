class SanPham:
    def __init__(
        self,
        ProductId    = None,
        ProductName  = None,
        Description  = None,
        Price        = None,
        OldPrice     = None,
        Quantity     = None,
        Rating       = 4.5,
        SoldCount    = 0,
        Emoji        = None,
        ImageUrl = None,
        CategoryId   = None,
        StoreId      = None,
        IsActive     = 1
    ):
        self.ProductId   = ProductId
        self.ProductName = ProductName
        self.Description = Description
        self.Price       = Price
        self.OldPrice    = OldPrice
        self.Quantity    = Quantity
        self.Rating      = Rating
        self.SoldCount   = SoldCount
        self.Emoji       = Emoji
        self.ImageUrl = ImageUrl
        self.CategoryId  = CategoryId
        self.StoreId     = StoreId
        self.IsActive    = IsActive