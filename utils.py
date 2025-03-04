from db import SessionLocal, db_logger, Product
from sqlalchemy import select
import logging

bot_logger = logging.getLogger(__name__)

FileHandler = logging.FileHandler(f'{__name__}.log', 'w')
FileHandler.setLevel(logging.DEBUG)

ConsoleHandler = logging.StreamHandler()
ConsoleHandler.setLevel(logging.DEBUG)

formater = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

FileHandler.setFormatter(formater)
ConsoleHandler.setFormatter(formater)

bot_logger.addHandler(FileHandler)
bot_logger.addHandler(ConsoleHandler)

async def get_str_product_list(page, obj, page_len):
    query = select(obj).limit(page_len).offset((page - 1) * page_len)
    async with SessionLocal() as session:
        try:
            result = await session.scalars(query)
        except Exception as e:
            db_logger.exception(f'get_str_product_list params: page: {page},obj: {obj}, page len: {page_len}\n'
                                f'query: {query}')

def product_to_dict(product):
    print('product_to_dict')
    dict_product = {column: getattr(product, column) for column in ['id', 'name', 'price', 'description', 'created_at', 'updated_at', 'quantity', 'seller_id']}
    return dict_product