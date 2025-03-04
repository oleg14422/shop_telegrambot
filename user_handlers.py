import logging
from aiogram.filters import Command
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram import F
from sqlalchemy import select, func

from callback_factory import ProductCallbackFactory, OrderCallbackFactory
from db import SessionLocal, Product, Order
from user_FMS import UserProductMenu, UserOrderMenu
from user_kbrd import user_start_kb, product_choose_kb, user_bool_kb, user_home_kb, user_orders_types, order_choose_kb

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

FileHandler = logging.FileHandler(f'{__name__}.log')
ConsoleHandler = logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ConsoleHandler.setFormatter(formatter)
FileHandler.setFormatter(formatter)

logger.addHandler(FileHandler)
logger.addHandler(ConsoleHandler)

logger.info(f'test the custom logger for module {__name__}')

user_router = Router()

@user_router.message(Command('start'))
async def user_start(message):
    await message.answer("Це бот для покупок, натисніть кнопку знизу щоб переглянути товари", reply_markup=user_start_kb())

@user_router.callback_query(F.data == 'user_home')
async def user_start_callback(callback):
    await callback.message.answer("Це бот для покупок, натисніть кнопку знизу щоб переглянути товари", reply_markup=user_start_kb())


@user_router.callback_query(F.data == 'user_product_menu')
async def user_product_menu_start(callback: CallbackQuery, state):
    await state.set_state(UserProductMenu.product_pick)
    async with SessionLocal() as session:
        count_records = await session.scalar(select(func.count()).select_from(Product))
        products = await session.scalars(select(Product).where(Product.quantity > 0).limit(10))
        kb_data = []
        msg = 'Виберіть продукт зі списку: \n'
        for product in products:
            kb_data.append({'text': product.name,
                            'product_id': product.id, })
            msg += f"Ім'я: {product.name}, ціна: {product.price}\n"

    is_next_page_bt = count_records > 10
    kb = product_choose_kb(kb_data, is_next_page_bt)
    await callback.message.answer(msg, reply_markup=kb)

    await callback.answer()


@user_router.callback_query(UserProductMenu.product_pick, F.data.in_(['next_page','prev_page']))
async def user_product_menu(callback: CallbackQuery, state):
    data = await state.get_data()
    offset = data.get('offset', 0)
    if callback.data == 'next_page':
        offset = offset + 10
    elif callback.data == 'prev_page':
        offset = offset - 10
        if offset < 0:
            offset = 0

    async with SessionLocal() as session:
        count_records = await session.scalar(select(func.count()).select_from(Product))
        products = await session.scalars(select(Product).where(Product.quantity > 0).offset(offset).limit(10))
        kb_data = []
        msg = 'Виберіть продукт зі списку: \n'
        for product in products:
            kb_data.append({'text': product.name,
                            'product_id': product.id, })
            msg += f"Ім'я: {product.name}, ціна: {product.price:.2f}\n"

    is_prev_page_bt = offset >= 10
    is_next_page_bt = count_records - offset > 10
    kb = product_choose_kb(kb_data, is_next_page_bt, is_prev_page_bt)
    await callback.message.edit_text(msg, reply_markup=kb)
    await state.update_data(offset=offset)
    await callback.answer()


@user_router.callback_query(UserProductMenu.product_pick ,ProductCallbackFactory.filter())
async def user_product_buy_confirm(callback: CallbackQuery, callback_data, state):
    product_id = callback_data.id
    await state.update_data(product_id=product_id)
    async with SessionLocal() as session:
        product = await session.get(Product, product_id)
        msg = '\n'.join([f'Назва {product.name}',
              f'Опис {product.description}',
              f'Ціна {product.price}',
              f'Бажаєте замовити?'
              ])

    await callback.message.answer(msg, reply_markup=user_bool_kb())
    await callback.answer()
    await state.set_state(UserProductMenu.confirm_product_buy)

@user_router.callback_query(UserProductMenu.confirm_product_buy)
async def user_product_buy_confirm(callback: CallbackQuery, state):
    data = await state.get_data()
    product_id = data['product_id']

    if callback.data != 'True':
        await callback.message.answer('Скасовано', reply_markup=user_home_kb())
        return

    async with SessionLocal() as session:
        product = await session.get(Product, product_id)
        if product.quantity < 1:
            await callback.message.answer('Нажаль сталася помилка, товару немає в наявності')
            await state.clear()
            await callback.answer(
                text='Немає в наявності',
                alert=True
            )
            return
        order = Order(product_id = product_id, buyer_id=callback.message.from_user.id, seller_id=product.seller_id)
        logger.debug(order)
        product.quantity -= 1
        session.add(product)
        session.add(order)
        await session.commit()

    await state.clear()
    await callback.message.answer('Успішно замовленно')
    await callback.answer(
        text = 'Замовлено',
        alert = True
    )



@user_router.callback_query(UserOrderMenu.pick_order, F.data.in_(['next_page', 'prev_page']))
@user_router.callback_query(F.data == 'user_orders')
async def user_all_orders(callback: CallbackQuery, state):
    await state.set_state(UserOrderMenu.pick_order)
    data = await state.get_data()
    offset = data.get('offset', 0)
    if callback.data == 'next_page':
        offset = offset + 10
    elif callback.data == 'prev_page':
        offset = offset - 10
    user_id = callback.message.from_user.id

    async with SessionLocal() as session:
        order_count = await session.scalar(select(func.count()).select_from(Order).where(Order.buyer_id == callback.message.from_user.id).where(Order.buyer_id == user_id))
        orders = await session.execute(select(Order.id, Product.name).join(Product).where(Order.buyer_id == user_id).offset(offset).limit(10))

        kb_data = []
        msg = 'Виберіть замовлення зі списку: \n'
        for order_id, product_name in orders:
            kb_data.append({'text': product_name,
                            'product_id': order_id, })
            msg += f"Номер замовлення: {order_id}, назва товару: {product_name}\n"

    await state.update_data(offset=offset)
    is_prev_page_bt = offset >= 10
    is_next_page_bt = order_count - offset > 10
    await callback.message.edit_text(msg, reply_markup=order_choose_kb(kb_data, is_next_page_bt, is_prev_page_bt))
    await callback.answer()

@user_router.callback_query(OrderCallbackFactory.filter())
async def show_user_order_info(callback: CallbackQuery, state, callback_data):
    order_id = callback_data.id
    logger.info(f'show_user_order {order_id}')
    async with SessionLocal() as session:
        result = await session.execute(select(Order.id, Product.name, Product.price, Product.description).join(Product))
        order_id, product_name, product_price, product_description = result.fetchone()
        logger.info(f'this is result {result}')
        if not order_id:
            await callback.message.answer('Сталася помилка, замовлення не знайденно', reply_markup=user_home_kb())
            await callback.answer(
                text='Сталася помилка',
                alert=True
            )
            await state.clear()
            return

        msg = '\n'.join([f'Номер замовлення {order_id}',
                         f'Назва товару {product_name}',
                         f'Ціна товару {product_price:.2f}',
                         f'Опис товару {product_description}',
                         ])

    await callback.message.answer(msg, reply_markup=user_home_kb())
    await callback.answer()