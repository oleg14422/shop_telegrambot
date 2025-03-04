from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class AddProduct(StatesGroup):
    name = State()
    price = State()
    description = State()
    quantity = State()
    confirm = State()

class ProductMenu(StatesGroup):
    product_pick = State()
    product_action = State()
    product_confirm_delete = State()
    edit_property = State()
    edit_name_property = State()
    edit_price_property = State()
    edit_quantity_property = State()
    edit_description_property = State()

class OrderMenu(StatesGroup):
    order_menu = State()