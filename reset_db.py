import asyncio

from beanie import init_beanie
from app.models import (
    Account,
    Operator,
    Plan,
    Order,
    Bundle,
    Product,
    ProdutionLine,
)
from loaders import mongo_client


async def main() -> None:
    await init_beanie(
        database=mongo_client.get_database(),
        document_models=[
            Account,
            Operator,
            Plan,
            Order,
            Bundle,
            Product,
            ProdutionLine,
        ],
    )

    await Plan.delete_all()
    await Order.delete_all()
    await Bundle.delete_all()
    await Product.delete_all()
    await Operator.delete_all()

    lines = await ProdutionLine.all().to_list()
    for line in lines:
        line.idle_log = []
        await line.save()


if __name__ == "__main__":
    asyncio.new_event_loop().run_until_complete(main())
