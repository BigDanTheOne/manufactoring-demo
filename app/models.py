from __future__ import annotations

from datetime import datetime, date
from pydantic import BaseModel, Field
from beanie import Document, BeanieObjectId
from app.enums import UserRole


class Plan_(BaseModel):
    orders: list[Order_ | BeanieObjectId] = Field(default=[])


class Order_(BaseModel):
    native_id: str = Field(alias="id")
    name: str
    bundles: list[Bundle_ | BeanieObjectId] = Field(default=[])
    production_line_id: str = Field(alias="productionLineId")
    total_mass: float = Field(alias="totalMass")
    total_length: float = Field(alias="totalLength")
    execution_time: int = Field(alias="executionTime")


class Bundle_(BaseModel):
    native_id: str = Field(alias="bundleId")
    products: list[Product_ | BeanieObjectId] = Field(default=[])
    total_mass: float = Field(alias="totalMass")
    total_length: float = Field(alias="totalLength")
    execution_time: int = Field(alias="executionTime")


class Product_(BaseModel):
    native_id: str = Field(alias="productId")
    profile: str
    width: float
    thickness: float
    length: float
    quantity: int
    color: str
    roll_number: int = Field(alias="rollNumber")


class Account(Document):
    tg_id: int | None = None
    phone: str
    role: str = UserRole.OPERATOR

    @staticmethod
    async def by_tg_id(tg_id: int) -> Account | None:
        return await Account.find_one(Account.tg_id == tg_id)

    @staticmethod
    async def by_phone(phone: str) -> Account | None:
        return await Account.find_one(Account.phone == phone)

    class Settings:
        name = "accounts"


class ProgressLog(BaseModel):
    product_id: BeanieObjectId
    count: int | float
    date: datetime


class Operator(Document):
    name: str
    rate: int | float
    line_id: BeanieObjectId
    progress_log: list[ProgressLog] = []

    class Settings:
        name = "operators"


class ProdutionLine(Document):
    name: str

    class Settings:
        name = "production_lines"


class Plan(Document):
    orders: list[BeanieObjectId]
    date: date

    @staticmethod
    async def get_current() -> Plan | None:
        return await Plan.find_one(Plan.date == datetime.now().date())

    async def get_orders(self) -> list[Order]:
        orders = []
        for order_id in self.orders:
            if order := await Order.get(order_id):
                orders.append(order)
        return orders

    class Settings:
        name = "plans"


class Order(Document):
    plan_id: BeanieObjectId
    native_id: str
    name: str
    bundles: list[BeanieObjectId]
    production_line_id: str
    total_mass: float
    total_length: float
    execution_time: int

    async def get_active_bundles(self) -> list[Bundle]:
        bundles = []
        for bundle_id in self.bundles:
            if bundle := await Bundle.get(bundle_id):
                if not bundle.finished:
                    bundles.append(bundle)
        return bundles

    class Settings:
        name = "orders"


class Bundle(Document):
    order_id: BeanieObjectId
    native_id: str
    products: list[BeanieObjectId]
    total_mass: float
    total_length: float
    execution_time: int
    finished: bool = False

    async def get_products(self) -> list[Product]:
        products = []
        for product_id in self.products:
            if product := await Product.get(product_id):
                products.append(product)
        return products

    class Settings:
        name = "bundles"


class Product(Document):
    bundle_id: BeanieObjectId
    native_id: str
    profile: str
    width: float
    thickness: float
    length: float
    quantity: int
    color: str
    roll_number: int

    class Settings:
        name = "products"
