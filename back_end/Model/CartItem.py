class CartItem:
    def __init__(self, CartId=None, ProductId=None, Quantity=0, UnitPrice=0):
        self.CartId = CartId
        self.ProductId = ProductId
        self.Quantity = Quantity
        self.UnitPrice = UnitPrice