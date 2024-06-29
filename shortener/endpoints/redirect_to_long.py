from datetime import datetime, timedelta, timezone
import pytz
from sqlalchemy.sql import func

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from shortener.db.connection import get_session
from shortener.db.models import UrlStorage, VipStorage


api_router = APIRouter(tags=["Url"])


@api_router.get(
    "/{short_code}",
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    responses={status.HTTP_404_NOT_FOUND: {"description": "URL `request.url` doesn't exist"}},
)
async def get_long_url(
    request: Request,
    short_code: str = Path(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Логика работы ручки:

    Проверяем, что у нас есть short_code в базе:
      - если он уже есть, то совершаем редирект на длинный урл + увеличиваем счетчик переходов на 1
      - если нет, то кидаем ошибку;
    """
    print("fofdongfnfnf")
    db_url_query = select(UrlStorage).where(UrlStorage.short_url == short_code).with_for_update()
    db_url = await session.scalar(db_url_query)
    if db_url:
        update_query = (
            update(UrlStorage)
            .where(UrlStorage.short_url == short_code)
            .values(number_of_clicks=db_url.number_of_clicks + 1)
        )
        await session.execute(update_query)
        await session.commit()
        print("-----------", db_url.long_url)
        return RedirectResponse(db_url.long_url)
    else:
        db_url_query = select(VipStorage).where(VipStorage.short_url == short_code).with_for_update()
        db_url = await session.scalar(db_url_query)
        if db_url:
            update_query = (
                update(VipStorage)
                .where(VipStorage.short_url == short_code)
                .values(number_of_clicks=db_url.number_of_clicks + 1)
            )
            time1 = db_url.dt_created + timedelta(seconds=db_url.url_expires)
            time2 = datetime.now() 
            time4 =( await session.execute(func.now()) ).scalar().replace(tzinfo=None)
            timeutc = ((time2 - time4).total_seconds() + 2) // 3600
            time3 = datetime.now() - timedelta(seconds=timeutc * 3600)
            if (time1 <= time3):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link is dead.")
            await session.execute(update_query)
            await session.commit()
            if (db_url.long_url.startswith("https://example.com")):
                return RedirectResponse("https://example.com")
            return RedirectResponse(db_url.long_url)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"URL '{request.url}' doesn't exist")
