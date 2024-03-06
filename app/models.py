from __future__ import annotations

from datetime import datetime, date
from pydantic import BaseModel, Field
from beanie import Document, BeanieObjectId
from app.enums import (
    UserRole,
    IdleType,
    ScheduledIdleReason,
    UnscheduledIdleReason,
)


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


class ShiftLog(BaseModel):
    start_time: datetime
    end_time: datetime | None = None


class Operator(Document):
    name: str
    rate: int | float
    line_id: BeanieObjectId
    progress_log: list[ProgressLog] = []
    shift_log: list[ShiftLog] = []

    async def start_shift(self) -> None:
        if self.shift_log[-1].end_time is None:
            return
        self.shift_log.append(ShiftLog(start_time=datetime.now()))
        await self.save()

    async def finish_shift(self) -> None:
        self.shift_log[-1].end_time = datetime.now()
        await self.save()

    class Settings:
        name = "operators"


class IdleLog(BaseModel):
    operator_id: BeanieObjectId
    start_time: datetime
    end_time: datetime | None = None
    type: IdleType
    reason: ScheduledIdleReason | UnscheduledIdleReason
    duration: datetime | None = None


class ProdutionLine(Document):
    name: str
    idle_log: list[IdleLog]

    async def start_idle(
        self,
        operator_id: BeanieObjectId,
        type: IdleType,
        reason: ScheduledIdleReason | UnscheduledIdleReason,
    ) -> None:
        self.idle_log.append(
            IdleLog(
                operator_id=operator_id,
                start_time=datetime.now(),
                type=type,
                reason=reason,
            )
        )
        await self.save()

    async def finish_idle(self) -> None:
        if self.idle_log[-1].duration:
            return
        start_time = self.idle_log[-1].start_time
        end_time = datetime.now()
        duration = end_time - start_time
        self.idle_log[-1].end_time = end_time
        self.idle_log[-1].duration = duration
        await self.save()

    class Settings:
        name = "production_lines"


class Plan(Document):
    orders: list[BeanieObjectId]
    date: date

    @staticmethod
    async def get_current() -> Plan | None:
        return await Plan.find_one(Plan.date == datetime.now().date())

    async def get_active_orders(self) -> list[Order]:
        orders = []
        for order_id in self.orders:
            if order := await Order.get(order_id):
                if not order.finished:
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
    finished: bool = False

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

    async def get_active_products(self) -> list[Product]:
        products = []
        for product_id in self.products:
            if product := await Product.get(product_id):
                if product.quantity > 1:
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
