import asyncio

from beanie import init_beanie
from app.models import Account, Operator, Plan, Order, Bundle, Product
from loaders import mongo_client


async def main() -> None:
    await init_beanie(
        database=mongo_client.get_database(),
        document_models=[Account, Operator, Plan, Order, Bundle, Product],
    )

    await Plan.delete_all()
    await Order.delete_all()
    await Bundle.delete_all()
    await Product.delete_all()


if __name__ == "__main__":
    asyncio.new_event_loop().run_until_complete(main())
