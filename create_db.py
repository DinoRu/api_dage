from app.db.session import engine, Base
from app.models.meter import Meter
from app.models.user import User


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    create_all_tables()