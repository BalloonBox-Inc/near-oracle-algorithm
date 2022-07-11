import aioredis
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter

from routers import plaid, coinbase, covalent, kyc


app = FastAPI()


# throttle control
@app.on_event('startup')
async def startup():
    redis = await aioredis.from_url('redis://localhost')
    await FastAPILimiter.init(redis)


# error handling
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({'error': exc.errors()})
    )


# validator routers
app.include_router(plaid.router)
app.include_router(coinbase.router)
app.include_router(covalent.router)


# kyc router - validator agnostic
app.include_router(kyc.router)
