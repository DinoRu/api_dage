import contextlib
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1.health_check import health_router
from app.api.v1.meter import router
from app.api.v1.user import user_router
from app.db.session import create_all_tables



@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await create_all_tables()
    yield

app = FastAPI(
    title="Дагэнержи Api",
    description="CMS for managing meters reading",
    version="0.0.1",
    contact={
        'name': "Diarra Moustapha",
        "email": "diarra.msa@gmail.com"
    },
    swagger_ui_parameters={
            "persistAuthorization": True
    },
    lifespan=lifespan
)

#Register the origins
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(router=health_router, prefix="/health check", tags=["health check"])
app.include_router(router=router, prefix="/meters", tags=['meters'])
app.include_router(router=user_router,  prefix="/users", tags=["users"])


if __name__ == "__main__":
    uvicorn.run("main:app", port=4000, reload=True)
