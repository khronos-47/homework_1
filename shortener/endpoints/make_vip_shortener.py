from datetime import timedelta
from enum import Enum
from random import choice
from string import ascii_uppercase, digits

from fastapi import APIRouter, Body, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from shortener import utils
from shortener.db.connection import get_session
from shortener.db.models import VipStorage
from shortener.schemas import MakeShorterRequest, MakeShorterResponse, VipUrlRequest, VipUrlResponse


class unit(str, Enum):
    DAYS = "DAYS"
    HOURS = "HOURS"
    MINUTES = "MINUTES"
    SECONDS = "SECONDS"


time = dict(
    {
        "DAYS": 86400,
        "HOURS": 3600,
        "MINUTES": 60,
        "SECONDS": 1,
    }
)
# UrlStorage
# MakeShorterResponse
api_router = APIRouter(tags=["Url"])


async def exist_check(session: AsyncSession, suffix: str) -> tuple[bool, str]:

    exist_query = select(exists().where(VipStorage.short_url == suffix))
    exist = await session.scalar(exist_query)
    short_url = utils.url_from_suffix(suffix)
    if exist:
        return True, suffix
    return False, suffix


@api_router.post(
    "/make_shorter1",
    response_model=VipUrlResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Site with this url does not exists or status code of request >= 400",
        },
    },
)
async def make_shorter(
    model: VipUrlRequest = Body(
        ..., example={"url": "https://yandex.ru", "vip_key": "my.ru", "time_to_live": 1, "time_to_live_unit": unit.DAYS}
    ),
    session: AsyncSession = Depends(get_session),
):
    print("-----------------", model)
    valid_site, message = await utils.check_website_exist(str(model.url))
    if not valid_site:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    check, suffix = await exist_check(session, utils.url_from_suffix(model.vip_key))
    if check:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vip short url already exist",
        )

    new_url = VipStorage(
        long_url=str(model.url),
        short_url=suffix,
        url_expires=int(model.time_to_live * time[model.time_to_live_unit.value]),
    )
    session.add(new_url)
    await session.commit()
    await session.refresh(new_url)
    new_url.short_url = utils.url_from_suffix(suffix)
    return VipUrlResponse.from_orm(new_url)
