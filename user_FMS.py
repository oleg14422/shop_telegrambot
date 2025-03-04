from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class UserProductMenu(StatesGroup):
    product_pick = State()
    confirm_product_buy = State()

class UserOrderMenu(StatesGroup):
    pick_type = State()
    pick_order  = State()