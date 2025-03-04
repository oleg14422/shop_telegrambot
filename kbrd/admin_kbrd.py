from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from callback_factory import ProductCallbackFactory



def start_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text = "Додати продукт➕",
        callback_data = 'add_product')
    )
    builder.row(InlineKeyboardButton(
        text = 'Продукти',
        callback_data = 'products')
    )
    builder.row(InlineKeyboardButton(
        text= 'Переглянути замовлення',
        callback_data = 'orders'
    ))
    builder.row(InlineKeyboardButton(
        text='Скасувати',
        callback_data = 'cancel'
    ))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def bool_kb():
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

def go_home_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='На головну',
        callback_data='home'
    ))
    return builder.as_markup()


def product_choose_kb(items: list, is_next_page: bool = False, is_prev_page: bool = False ):
    builder = InlineKeyboardBuilder()

    # Додаємо кнопки вибору сторінки (якщо є)
    nav_buttons = []
    if is_prev_page:
        nav_buttons.append(
            InlineKeyboardButton(text="Попередня сторінка", callback_data="prev_page")
        )
    if is_next_page:
        nav_buttons.append(
            InlineKeyboardButton(text="Наступна сторінка", callback_data="next_page")
        )

    # Додаємо кнопки вибору сторінки в одному рядку
    if nav_buttons:
        builder.row(*nav_buttons)

    # Додаємо інші кнопки у стовпчик
    for item in items:
        builder.button(
            text=item["text"],
            callback_data=ProductCallbackFactory(id=item["product_id"])
        )

    return builder.adjust(2 if len(nav_buttons) == 2 else 1, 1).as_markup()

def product_action_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='Видалити',
        callback_data='delete_product'
    ))
    builder.row(InlineKeyboardButton(
        text='Змінити',
        callback_data='edit_product'
    ))
    builder.row(InlineKeyboardButton(
            text='Скасувати❌',
            callback_data='cancel'
    ))
    return builder.as_markup()

def product_property_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text='Назва',
        callback_data='product_name_property'
    ))
    builder.row(InlineKeyboardButton(
        text='Ціна',
        callback_data='product_price_property'
    ))
    builder.row(InlineKeyboardButton(
        text='Опис',
        callback_data='product_description_property'
    ))
    builder.row(InlineKeyboardButton(
        text='Кількість',
        callback_data='product_quantity_property'
    ))

    builder.row(InlineKeyboardButton(
        text='Скасувати❌',
        callback_data='cancel'
    ))
    return builder.as_markup()