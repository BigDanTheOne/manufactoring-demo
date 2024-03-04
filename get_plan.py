import asyncio

from datetime import datetime
from beanie import init_beanie
from app.models import Account, Operator, Plan, Order, Bundle, Product
from loaders import mongo_client
from api import API


async def main() -> None:
    await init_beanie(
        database=mongo_client.get_database(),
        document_models=[Account, Operator, Plan, Order, Bundle, Product],
    )

    api = API()
    plan = api.get_plan()

    new_plan = Plan(orders=[], date=datetime.now().date())
    await new_plan.insert()

    for order in plan.orders:
        new_order = Order(
            plan_id=new_plan.id,
            native_id=order.native_id,
            name=order.name,
            bundles=[],
            production_line_id=order.production_line_id,
            total_mass=order.total_mass,
            total_length=order.total_length,
            execution_time=order.execution_time,
        )
        await new_order.insert()
        new_plan.orders.append(new_order.id)

        for bundle in order.bundles:
            new_bundle = Bundle(
                order_id=new_order.id,
                native_id=bundle.native_id,
                products=[],
                total_mass=bundle.total_mass,
                total_length=bundle.total_length,
                execution_time=bundle.execution_time,
            )
            await new_bundle.insert()
            new_order.bundles.append(new_bundle.id)

            for product in bundle.products:
                new_product = Product(
                    bundle_id=new_bundle.id,
                    native_id=product.native_id,
                    profile=product.profile,
                    width=product.width,
                    thickness=product.thickness,
                    length=product.length,
                    quantity=product.quantity,
                    color=product.color,
                    roll_number=product.roll_number,
                )
                await new_product.insert()
                new_bundle.products.append(new_product.id)
            await new_bundle.save()
        await new_order.save()
    await new_plan.save()


if __name__ == "__main__":
    asyncio.new_event_loop().run_until_complete(main())
