import asyncio
import httpx
import pytest
from main import app
from app.models.meter import Meter
from app.models.user import User


@pytest.fixture(scope="session")
async def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


def init_db():
    pass
