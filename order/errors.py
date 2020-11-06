class OrderError(Exception):
    pass

class EncodeError(OrderError):
    pass
class DecodeError(OrderError):
    pass