from db import Admin, SessionLocal
import asyncio
print('success')

async def add_admin(telegram_id):
    async with SessionLocal() as session:
        admin = Admin(telegram_id=telegram_id)
        session.add(admin)
        await session.commit()

async def see_admins():
    async with SessionLocal() as session:

        for admin in admins:
            print(admin.telegram_id)


asyncio.run(see_admins())