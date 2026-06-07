class OrderItem:
    def __init__(self, OrderItemId=None, OrderId=None, ProductId=None, ProductName=None,
                 Emoji=None, Quantity=0, UnitPrice=0, TotalPrice=0):
        self.OrderItemId = OrderItemId
        self.OrderId = OrderId
        self.ProductId = ProductId
        self.ProductName = ProductName
        self.Emoji = Emoji
        self.Quantity = Quantity
        self.UnitPrice = UnitPrice
        self.TotalPrice = TotalPrice