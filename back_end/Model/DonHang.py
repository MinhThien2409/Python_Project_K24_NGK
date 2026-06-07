class DonHang:
    def __init__(self, OrderId=None, Status='Pending', ShippingFee=0, CartId=None,
                 UserId=None, ReceiverName=None, ReceiverPhone=None, ShippingAddress=None,
                 PaymentMethod='COD', VoucherCode=None, SubTotal=0, DiscountAmount=0,
                 TotalAmount=0, Note=None, CreatedAt=None, UpdatedAt=None,Discount=None):
        self.OrderId = OrderId
        self.Status = Status
        self.ShippingFee = ShippingFee
        self.CartId = CartId
        self.UserId = UserId
        self.ReceiverName = ReceiverName
        self.ReceiverPhone = ReceiverPhone
        self.ShippingAddress = ShippingAddress
        self.PaymentMethod = PaymentMethod
        self.VoucherCode = VoucherCode
        self.SubTotal = SubTotal
        self.DiscountAmount = DiscountAmount
        self.TotalAmount = TotalAmount
        self.Note = Note
        self.CreatedAt = CreatedAt
        self.UpdatedAt = UpdatedAt

        # Danh sách chứa các OrderItem
        self.Items = []