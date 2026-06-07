class GioHang:
    def __init__(self, CartId=None, UserId=None, TotalAmount=0, CreatedAt=None):
        self.CartId = CartId
        self.UserId = UserId
        self.TotalAmount = TotalAmount
        self.CreatedAt = CreatedAt
        self.Items = []  # Danh sách chứa các đối tượng CartItem