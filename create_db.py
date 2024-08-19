from app.db.session import engine, Base
from app.models.meter import Meter
from app.models.user import User


print("Creating db...")
Base.metadata.create_all(engine)
