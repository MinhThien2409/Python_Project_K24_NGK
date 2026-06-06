class YeuCau:
    def __init__(self, RequestId=None, UserId=None, ShopName=None,
                 BusinessPhone=None, Category=None, Description=None,
                 NationalId=None, Status='pending',
                 CreatedAt=None, ReviewedBy=None,
                 ReviewedAt=None, RejectReason=None):
        self.RequestId     = RequestId
        self.UserId        = UserId
        self.ShopName      = ShopName
        self.BusinessPhone = BusinessPhone
        self.Category      = Category
        self.Description   = Description
        self.NationalId    = NationalId
        self.Status        = Status
        self.CreatedAt     = CreatedAt
        self.ReviewedBy    = ReviewedBy
        self.ReviewedAt    = ReviewedAt
        self.RejectReason  = RejectReason