class GioHang:
    def __init__(self, CartId=None, UserId=None, TotalAmount=0, CreatedAt=None):
        """Khởi tạo giỏ hàng của người dùng cùng danh sách mặt hàng."""
        self.CartId = CartId
        self.UserId = UserId
        self.TotalAmount = TotalAmount
        self.CreatedAt = CreatedAt
        self.Items = []  # Danh sách chứa các đối tượng CartItem