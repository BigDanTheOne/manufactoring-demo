from __future__ import annotations

import os
import logging
import json

from datetime import datetime
from pprint import pprint
from pydantic import BaseModel, Field, ValidationError
from beanie import Document, PydanticObjectId
from beanie.operators import In, RegEx
from aiogram.types import BufferedInputFile

from app.enums import UserRole
from loaders import bot


class User(Document):
    tg_id: int | None = None
    phone: str
    role: str = UserRole.OPERATOR

    @staticmethod
    async def by_tg_id(tg_id: int) -> User | None:
        return await User.find_one(User.tg_id == tg_id)

    @staticmethod
    async def by_phone(phone: str) -> User | None:
        return await User.find_one(User.phone == phone)

    class Settings:
        name = "users"


class Employee(Document):
    name: str
    rate: int | float

    class Settings:
        name = "employees"


class Plan(BaseModel):
    orders: list[Order]

    @staticmethod
    def get_plan() -> Plan:
        json_file = open("response.example.json", "r")
        response = '{"orders": ' + json_file.read() + "}"

        try:
            result = Plan.model_validate_json(response)
        except ValidationError as e:
            pprint(json.loads(e.json()))
        else:
            return result

    def get_order(self, id: str) -> Order | None:
        for order in self.orders:
            if order.id == id:
                return order
        return None


class Order(BaseModel):
    id: str
    name: str
    bundles: list[Bundle]
    production_line_id: str = Field(alias="productionLineId")
    total_mass: float = Field(alias="totalMass")
    total_length: float = Field(alias="totalLength")
    execution_time: int = Field(alias="executionTime")

    def get_bundle(self, id: str) -> Bundle | None:
        for bundle in self.bundles:
            if bundle.id == id:
                return bundle
        return None


class Bundle(BaseModel):
    id: str = Field(alias="bundleId")
    products: list[Product]
    total_mass: float = Field(alias="totalMass")
    total_length: float = Field(alias="totalLength")
    execution_time: int = Field(alias="executionTime")


class Product(BaseModel):
    id: str = Field(alias="productId")
    profile: str
    width: float
    thickness: float
    length: float
    quantity: int
    color: str
    roll_number: int = Field(alias="rollNumber")
