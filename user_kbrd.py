from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from callback_factory import ProductCallbackFactory, OrderCallbackFactory


def user_start_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text = 'Переглянути товари',
        callback_data = 'user_product_menu'
    ))
    builder.row(InlineKeyboardButton(
        text = 'Переглянути замовлення',
        callback_data = 'user_orders'
    ))

    return builder.as_markup()


def product_choose_kb(items: list, is_next_page: bool = False, is_prev_page: bool = False ):
    builder = InlineKeyboardBuilder()


    nav_buttons = []
    if is_prev_page:
        nav_buttons.append(
            InlineKeyboardButton(text="Попередня сторінка", callback_data="prev_page")
        )
    if is_next_page:
        nav_buttons.append(
            InlineKeyboardButton(text="Наступна сторінка", callback_data="next_page")
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    for item in items:
        builder.button(
            text=item["text"],
            callback_data=ProductCallbackFactory(id=item["product_id"])
        )

    return builder.adjust(2 if len(nav_buttons) == 2 else 1, 1).as_markup()

def user_bool_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text='Так✅',
        callback_data='True')
    )
    builder.add(InlineKeyboardButton(
        text='Ні❌',
        callback_data='False')
    )
    return builder.as_markup(one_time_keyboard=True)

def user_home_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text='Головна',
            callback_data='user_home'
        )
    )

def user_orders_types():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text='Всі замовлення',
            callback_data='user_orders'
        )
    )
    builder.row(
        InlineKeyboardButton(
            text='Назад',
            callback_data='user_home'
        )
    )
    return builder.as_markup()

def order_choose_kb(items: list, is_next_page: bool = False, is_prev_page: bool = False ):
    builder = InlineKeyboardBuilder()


    nav_buttons = []
    if is_prev_page:
        nav_buttons.append(
            InlineKeyboardButton(text="Попередня сторінка", callback_data="prev_page")
        )
    if is_next_page:
        nav_buttons.append(
            InlineKeyboardButton(text="Наступна сторінка", callback_data="next_page")
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    for item in items:
        builder.button(
            text=item["text"],
            callback_data=OrderCallbackFactory(id=item["product_id"])
        )

    return builder.adjust(2 if len(nav_buttons) == 2 else 1, 1).as_markup()
