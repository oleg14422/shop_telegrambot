from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from callback_factory import ProductCallbackFactory
from db import db_logger, Product, Admin, SessionLocal, FileHandler, Order
from middlewares.admin_middlewares import IsAdminMiddleware, DeleteKbMiddleware
from kbrd.admin_kbrd import start_kb, bool_kb, go_home_kb, product_choose_kb, product_action_kb, product_property_kb
from aiogram import F
import logging
from FMS.admin_FMS import AddProduct, ProductMenu, OrderMenu
import json
from utils import product_to_dict
import logging
from dataclasses import dataclass

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


db_logger.info('Imported')
admin_router = Router()
admins = [678120082]
admin_router.message.middleware(IsAdminMiddleware(admins))

@admin_router.callback_query(F.data.lower() == 'cancel')
async def cancel_admin_handler(callback, state, bot):
    await state.clear()
    await callback.message.answer('Скасовано', reply_markup=go_home_kb())
    await callback.answer()

@admin_router.callback_query(F.data == 'home')
async def start_admin_callback_handler(callback: types.CallbackQuery):
    await callback.message.answer(f'hello, your id is: {callback.message.from_user.id}', reply_markup=start_kb())
    await callback.answer()

@admin_router.message(Command('admin'))
async def admin_start_handler(message, bot):
    await message.answer(f'hello, your id is: {message.from_user.id}', reply_markup=start_kb())

    db_logger.info('start')

@admin_router.callback_query(F.data == 'add_product')
async def add_product_handler(callback: types.CallbackQuery, bot, state: FSMContext):
    await callback.message.answer('Введіть назву товару')
    await state.set_state(AddProduct.name)
    await callback.answer()

@admin_router.message(AddProduct.name)
async def add_product_name_handler(message, bot, state: FSMContext):
    name = message.text
    await message.answer("Введіть ціну товару", reply_markup=go_home_kb())
    await state.update_data(name=name)
    await state.set_state(AddProduct.price)

@admin_router.message(AddProduct.price)
async def add_product_price_handler(message, bot, state: FSMContext):
    price = message.text
    try:
        price = float(price)
        if price <0:
            await message.answer('Має бути невід\'ємне число')
            return
    except ValueError:
        await message.answer('Повинно бути число')
        return
    await message.answer("Введіть опис товару", reply_markup=go_home_kb())
    await state.update_data(price=price)
    await state.set_state(AddProduct.description)

@admin_router.message(AddProduct.description)
async def add_product_description_handler(message, bot, state: FSMContext):
    description = message.text
    await message.answer('Введіть кількість', reply_markup=go_home_kb())
    delete_kb = True
    await state.update_data(description=description)
    await state.set_state(AddProduct.quantity)

@admin_router.message(AddProduct.quantity)
async def add_product_quantity_handler(message, bot, state: FSMContext):
    quantity = message.text
    try:
        quantity = int(quantity)
        if quantity <0:
            await message.answer('Має бути невід\'ємне число',reply_markup=go_home_kb())
            return
    except ValueError:
        await message.answer("Введіть ціле число", reply_markup=go_home_kb())
        return
    data = await state.get_data()
    name, price, description= data['name'], data['price'], data['description']
    await state.update_data(quantity=quantity)
    await message.answer(f'Назва товару: {name}\n'
                         f'Ціна товару: {price}\n'
                         f'Опис товару: {description}\n'
                         f'Кількість товару: {quantity}\n'
                         'Ви впевненні що хочете додати його?', reply_markup=bool_kb())
    await state.set_state(AddProduct.confirm)

@admin_router.callback_query(AddProduct.confirm, F.data=='True')
async def add_product_confirm_handler(callback: types.CallbackQuery, bot, state: FSMContext):
    await callback.message.edit_reply_markup()
    data = await state.get_data()
    name, price, description, quantity= data['name'], data['price'], data['description'], data['quantity']
    async with SessionLocal() as session:
        try:
            product = Product(name=name, price=price, description=description, quantity=quantity, seller_id=callback.message.from_user.id)
            session.add(product)
            await session.commit()
        except Exception as e:
            await session.rollback()
            db_logger.exception(f'User data: \n{json.dumps(data)}')
            await callback.answer(
                text='Нажаль, сталася помилка',
                show_alert=True,
            )
            return
    await callback.answer(
        text='Успішно додано',
        show_alert=True
    )
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=go_home_kb())


@admin_router.callback_query(AddProduct.confirm, F.data=='False')
async def add_product_confirm_handler(callback: types.CallbackQuery, bot, state: FSMContext):
    await callback.message.edit_reply_markup()
    await state.clear()
    await callback.answer(
        text='Додавання товару скасовано',
        show_alert=True
    )

@admin_router.callback_query(F.data == 'cancel', F.state.func(lambda state: state.group == AddProduct))
async def add_product_cancel_callback_handler(callback: types.CallbackQuery, bot, state: FSMContext):
    await callback.message.edit_reply_markup()
    await callback.message.answer("Скасовано", reply_markup=start_kb())
    await state.clear()

@admin_router.message(Command('cancel'), F.state.func(lambda state: state.group == AddProduct))
async def add_product_cancel_message_handler(message: types.Message, bot, state: FSMContext):
    await message.edit_reply_markup()
    await message.answer("Скасовано", reply_markup=start_kb())
    await state.clear()


@admin_router.callback_query(F.data == 'products')
async def prouduct_menu_start_handler(callback: types.CallbackQuery, bot, state: FSMContext):
    await callback.message.edit_reply_markup()
    async with SessionLocal() as session:
        count_records = await session.scalar(select(func.count()).select_from(Product))
        products = await session.scalars(select(Product).limit(10))
        kb_data = []
        msg = 'Виберіть продукт зі списку: \n'
        for product in products:
            kb_data.append({'text': product.name,
                            'product_id': product.id,})
            msg += f"Ім'я: {product.name}, ціна: {product.price}\n"

    is_next_page_bt = count_records > 10
    kb = product_choose_kb(kb_data, is_next_page_bt)
    await callback.message.answer(msg, reply_markup=kb)
    await state.set_state(ProductMenu.product_pick)
    await callback.answer()

@admin_router.callback_query(F.data == 'prev_page', ProductMenu.product_pick)
@admin_router.callback_query(F.data == 'next_page', ProductMenu.product_pick)
async def product_menu_handler(callback: types.CallbackQuery, bot, state: FSMContext):
    data = await state.get_data()
    offset = data.get('offset', 0)
    if callback.data == 'prev_page':
        offset -= 10
        if offset < 0:
            offset = 0
    elif callback.data == 'next_page':
        offset += 10

    await state.update_data(offset=offset)

    async with SessionLocal() as session:
        count_records = await session.scalar(select(func.count()).select_from(Product))
        products = await session.scalars(select(Product).limit(10).offset(offset))
        kb_data = []
        msg = 'Виберіть продукт зі списку: \n'
        for product in products:
            kb_data.append({'text': product.name,
                            'product_id': product.id, })
            msg += f"Ім'я: {product.name}, ціна: {product.price}\n"

    last_product_num = offset + 10 if offset + 10 < count_records else count_records
    msg += f'Показано товари з {offset+1} по {last_product_num+1}'
    is_next_page_bt: bool = count_records - offset > 10
    is_prev_page_bt: bool = offset >= 10
    kb = product_choose_kb(kb_data, is_next_page_bt, is_prev_page_bt)
    await callback.message.edit_text(msg)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@admin_router.callback_query(ProductMenu.product_pick, ProductCallbackFactory.filter())
async def product_action_pick_handler(callback: types.CallbackQuery, callback_data ,bot, state: FSMContext):
    await callback.message.edit_reply_markup()
    product_id = callback_data.id
    logger.info(f'product id {product_id}')

    async with SessionLocal() as session:
        try:
            product = await session.scalar(select(Product).where(Product.id == product_id))
            dict_product = product_to_dict(product)
            msg = "\n".join([
                f"Назва продукту: {product.name}",
                f"Ціна: {product.price}",
                f"Опис: {product.description}",
                f"Опис: {product.quantity}",
                "Виберіть дію з продуктом"
            ])
        except:
            logger.exception('error in product_action_pick_handler in db session')
            await callback.message.answer('Нажаль, сталася помилка')
            await state.clear()
            return

    logger.debug(msg)
    await state.set_state(ProductMenu.product_action)
    await state.update_data(product_id=product_id, dict_product=dict_product)
    await callback.message.answer(msg, reply_markup=product_action_kb())
    await callback.answer()


@admin_router.callback_query(ProductMenu.product_action, F.data == 'delete_product')
async def delete_product_handler(callback: types.CallbackQuery, bot, state: FSMContext):
    data = await state.get_data()
    product_id = data.get('product_id', None)
    if not product_id:
        await callback.message.answer('Нажаль сталася помилка')
        await state.clear()
        return
    msg = 'Ви впевненні що хочете видалити продукт?'

    await callback.message.answer(msg, reply_markup=bool_kb())
    await callback.answer()
    await state.set_state(ProductMenu.product_confirm_delete)

@admin_router.callback_query(ProductMenu.product_confirm_delete)
async def confirm_delete_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'False':
        await callback.message.answer('Скасовано')
        await state.clear()
        return
    data = await state.get_data()
    product_id = data['product_id']
    async with SessionLocal() as session:
        product = await session.get(Product, product_id)
        await session.delete(product)
        await session.commit()

    await callback.message.answer("Успішно видалено")
    await state.clear()
    await callback.answer()

@admin_router.callback_query(ProductMenu.product_action, F.data == 'edit_product')
async def choose_product_property_handler(callback: types.CallbackQuery, bot, state: FSMContext):
    data = await state.get_data()
    logger.debug('choose_product_property_handler')
    product = data['dict_product']
    msg = '\n'.join(['Виберіть властивість товару яку ви хочете змінити',
                    f'Назва {product.get("name")}',
                    f'Ціна {float(product.get("price")):.2f}',
                    f'Опис {product.get("description")}',
                    f'Кількість {product.get("quantity")}',
                     ])
    await state.set_state(ProductMenu.edit_property)
    await callback.message.answer(msg, reply_markup=product_property_kb())
    await callback.answer()


@admin_router.callback_query(ProductMenu.edit_property)
async def edit_product_name(callback: types.CallbackQuery, bot, state: FSMContext):
    if callback.data == 'product_name_property':
        await callback.message.answer('Введіть нову назву товару')
        await state.set_state(ProductMenu.edit_name_property)
    elif callback.data == 'product_price_property':
        await callback.message.answer('Введіть нову ціну товару')
        await state.set_state(ProductMenu.edit_price_property)
    elif callback.data == 'product_quantity_property':
        await callback.message.answer('Введіть нову кількість товару')
        await state.set_state(ProductMenu.edit_quantity_property)
    elif callback.data == 'product_description_property':
        await callback.message.answer('Введіть новий опис товару')
        await state.set_state(ProductMenu.edit_description_property)

    await callback.answer()

@admin_router.message(ProductMenu.edit_name_property)
async def edit_name_property(message: types.Message, bot, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']
    async with SessionLocal() as session:
        product = await session.get(Product, product_id)
        try:
            product.name = message.text
            await session.commit()
        except:
            logger.exception(f'error in edit_name_property product_id {product_id}, new name {message.text}')
            await message.answer('Нажаль сталася помилка при зміні назви')
            await state.clear()
            return

    await message.answer('Назва успішно змінена', reply_markup=start_kb())
    await state.clear()

@admin_router.message(ProductMenu.edit_price_property)
async def edit_price_property(message: types.Message, bot, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']
    try:
        new_price = float(message.text)
    except:
        await message.answer('Вкажіть дійсне число, дробова частина вказується через крапку а не через кому')
        return

    async with SessionLocal() as session:
        try:
            product = await session.get(Product, product_id)
            product.price = new_price
            await session.commit()
        except:
            logger.exception(f'error in edit_price_property product_id {product_id}, new price {message.text}')
            await message.answer('Нажаль сталася помилка при зміні ціни')
            await state.clear()
            return

    await message.answer('Ціна успішно змінена', reply_markup=start_kb())
    await state.clear()


@admin_router.message(ProductMenu.edit_quantity_property)
async def edit_quantity_property(message: types.Message, bot, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']
    try:
        new_quantity = int(message.text)
    except:
        await message.answer('Вкажіть ціле')
        return

    async with SessionLocal() as session:
        try:
            product = await session.get(Product, product_id)
            product.quantity = new_quantity
            await session.commit()
        except:
            logger.exception(f'error in edit_quantity_property product_id {product_id}, new quantity {message.text}')
            await message.answer('Нажаль сталася помилка при зміні кількості')
            await state.clear()
            return

    await message.answer("Кількість успішно змінена")
    await state.clear()

@admin_router.message(ProductMenu.edit_description_property)
async def edit_description_property(message: types.Message, bot, state: FSMContext):
    data = await state.get_data()
    product_id = data['product_id']

    async with SessionLocal() as session:
        product = await session.get(Product, product_id)
        product.description = message.text
        await session.commit()

    await message.answer("Опис товару змінено")

@admin_router.callback_query(OrderMenu.order_menu ,F.data.in_(['next_page', 'prev_page']))
@admin_router.callback_query(F.data == 'orders')
async def admin_orders(callback, state):
    await state.set_state(OrderMenu.order_menu)
    data = await state.get_data()
    offset = data.get('offset', 0)
    if callback.data == 'next_page':
        offset+= 10
    elif callback.data == 'prev_page':
        offset -= 10

    async with SessionLocal() as session:
        orders_count = await session.scalar(select(func.count()).select_from(Order))
        logger.info(f'order count: {orders_count}')
        orders = await session.execute(select(Order.id, Order.buyer_id, Product.name).join(Product))

        kb_data = []
        msg = 'Виберіть замовлення зі списку: \n'
        for order_id, buyer_id, product_name in orders:
            kb_data.append({'text': product_name,
                            'product_id': order_id, })
            msg += f"Ім'я: {product_name}, номер замовлення: {order_id}, customer tg id {buyer_id}\n"
    await callback.message.answer(msg, reply_markup=product_choose_kb(kb_data))
    await callback.answer()

@admin_router.callback_query(OrderMenu.order_menu, ProductCallbackFactory.filter())
async def order_view(callback, state: FSMContext, callback_data):
    order_id = callback_data.id
    async with SessionLocal() as session:
        query = select(Product.name, Product.price, Product.description, Order.id, Order.buyer_id).join(Order)
        query_result = await session.execute(query)
        name, price, description, order_id, buyer_id = query_result.fetchone()
    msg = '\n'.join([
        f'Назва товару {name}',
        f'Ціна {price:.2f}',
        f'Опис {description}',
        f'Номер замовлення {order_id}',
        f'tg id покупця {buyer_id}'
    ])
    await callback.message.edit_text(msg, reply_markup=start_kb())