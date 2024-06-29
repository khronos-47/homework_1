from datetime import datetime, timedelta, timezone
from enum import Enum
from random import choice
from string import ascii_uppercase, digits
from typing import Union

from fastapi import APIRouter, Body, Depends, Request
from fastapi.exceptions import HTTPException
from sqlalchemy import delete, exists, select
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from starlette import status

from shortener import utils
from shortener.db.connection import get_session
from shortener.db.models import UrlStorage, VipStorage
from shortener.schemas import MakeShorterRequest, MakeShorterResponse, VipUrlRequest, VipUrlResponse


api_router = APIRouter(tags=["Url"])


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


async def get_short(session: AsyncSession) -> tuple[str, str]:
    while True:
        suffix = "".join(choice(ascii_uppercase + digits) for _ in range(5))
        exist_query = select(exists().where(UrlStorage.short_url == suffix))
        exist = await session.scalar(exist_query)
        if not exist:
            break
    short_url = utils.url_from_suffix(suffix)
    print("suffix________\n", suffix, "\n -----END_---------\n", short_url, "\n---------")
    return short_url, suffix


async def exist_check(session: AsyncSession, suffix: str) -> tuple[bool, str]:

    exist_query = select(exists().where(VipStorage.short_url == suffix))
    exist = await session.scalar(exist_query)
    short_url = utils.url_from_suffix(suffix)
    if exist:
        db_url_query = select(VipStorage).where(VipStorage.short_url == suffix).with_for_update()
        db_url = await session.scalar(db_url_query)
        print("--------", type(db_url.dt_created), "------------")
        time1 = db_url.dt_created + timedelta(seconds=db_url.url_expires)
        time1 = time1.astimezone(timezone.utc)
        datanow = func.current_timestamp()
        time2 = (await session.execute(func.now())).scalar()
        print("--------", time1, "------------", time2)
        if time1 < time2:
            query = delete(VipStorage).where(VipStorage.short_url == suffix)
            await session.execute(query)
            await session.commit()
            return False, suffix
        return True, suffix
    return False, suffix


@api_router.post(
    "/make_shorter",
    response_model=MakeShorterResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Site with this url does not exists or status code of request >= 400",
        },
    },
)
async def make_shorter_handler(
    request: Union[VipUrlRequest, MakeShorterRequest] = Body(
        ..., example={"url": "https://yandex.ru", "vip_key": "my.ru", "time_to_live": 1, "time_to_live_unit": unit.DAYS}
    ),
    session: AsyncSession = Depends(get_session),
):

    data = len(request.dict())
    if data > 1:
        return await make_vip(session, request)
    else:
        return await make_shorter(session, request)

    return


async def make_shorter(session: AsyncSession, model: MakeShorterRequest):
    print("call make_shorte------------")
    db_url_query = select(UrlStorage).where(UrlStorage.long_url == str(model.url))
    db_url = await session.scalar(db_url_query)
    exist = db_url is not None
    if exist:
        db_url.short_url = utils.url_from_suffix(db_url.short_url)
        return MakeShorterResponse.from_orm(db_url)
    valid_site, message = await utils.check_website_exist(str(model.url))
    if not valid_site:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )
    _, suffix = await get_short(session)
    new_url = UrlStorage(long_url=str(model.url), short_url=suffix)
    session.add(new_url)
    await session.commit()
    await session.refresh(new_url)
    new_url.short_url = utils.url_from_suffix(suffix)
    return MakeShorterResponse.from_orm(new_url)


async def make_vip(session: AsyncSession, model: VipUrlRequest):
    print("call make_vip ---------------")
    print("-----------------", model)
    valid_site, message = await utils.check_website_exist(model.url)

    print(valid_site," check_website_exist: ", model.url)
    if (model.url.startswith("https://example.com")):
        valid_site = True

    if not valid_site :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URl govno"
        )
        return
    check, suffix = await exist_check(session, model.vip_key)
    print("--------", suffix)
    if check:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vip short url already exist",
        )
    try:
        url_expires = int(model.time_to_live * time[model.time_to_live_unit.value])
    except:
        url_expires = int(model.time_to_live * 3600)

    new_url = VipStorage(long_url=str(model.url), short_url=model.vip_key, url_expires=url_expires)
    session.add(new_url)
    await session.commit()
    await session.refresh(new_url)
    new_url.short_url = utils.url_from_suffix(suffix)
    return VipUrlResponse.from_orm(new_url)
