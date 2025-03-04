from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, DeclarativeBase, backref, relationship, sessionmaker
import asyncio
import logging

db_logger = logging.getLogger('db.log')
db_logger.setLevel(logging.DEBUG)

FileHandler = logging.FileHandler('db.log')
FileHandler.setLevel(logging.INFO)

ConsoleHandler = logging.StreamHandler()
ConsoleHandler.setLevel(logging.DEBUG)

formater = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

FileHandler.setFormatter(formater)
ConsoleHandler.setFormatter(formater)

db_logger.addHandler(FileHandler)
db_logger.addHandler(ConsoleHandler)

from typing_extensions import override

database_url = 'sqlite+aiosqlite:///./test.db'
engine = create_async_engine(database_url, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, autoflush=False, autocommit=False)
Base = declarative_base()

class Product(Base):
    __tablename__ = 'product'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    price: Mapped[float] = mapped_column(Numeric, nullable=False)
    description: Mapped[str] = mapped_column(String(256), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime,  default=datetime.today, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.today, onupdate=datetime.today, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey('admin.telegram_id'), nullable=False )
    seller: Mapped["Admin"] = relationship("Admin", back_populates="products")
    orders: Mapped["Order"] = relationship("Order", back_populates="product")

    def __repr__(self):
        return f'<Base product id: {self.id}, name: {self.name}, price: {self.price}, quantity: {self.quantity}, seller_id: {self.seller_id}, created_at: {self.created_at}>'


class Admin(Base):
    __tablename__ = 'admin'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    products: Mapped[list['Product']] = relationship("Product", back_populates="seller")


class Order(Base):
    __tablename__ = 'order'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey('admin.telegram_id'),nullable=False)
    buyer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('product.id'),nullable=False)
    product: Mapped["Product"] = relationship("Product", back_populates="orders")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)