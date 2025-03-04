from aiogram.filters.callback_data import CallbackData

class ProductCallbackFactory(CallbackData, prefix='product'):
    id: int = None

class OrderCallbackFactory(CallbackData, prefix='order'):
    id: int = None


