from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Path
from fastapi.exceptions import HTTPException
from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import TIME
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from starlette import status

from shortener.db.connection import get_session
from shortener.db.models import UrlStorage, VipStorage
from shortener.schemas import GetInfoAboutLinkResponse
from shortener.utils import url_from_suffix


api_router = APIRouter(tags=["Url"])


@api_router.get(
    "/admin/{secret_key}",
    status_code=status.HTTP_200_OK,
    response_model=GetInfoAboutLinkResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Link with this secret key is not found.",
        }
    },
)
async def get_info_about_link(
    secret_key: UUID4 = Path(...),
    session: AsyncSession = Depends(get_session),
):

    db_url_query = select(UrlStorage).where(UrlStorage.secret_key == secret_key)
    db_url = await session.scalar(db_url_query)
    if db_url is None:
        db_url_query = select(VipStorage).where(VipStorage.secret_key == secret_key)
        db_url = await session.scalar(db_url_query)
        if db_url is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link with this secret key is not found.",
            )
        time1 = db_url.dt_created + timedelta(seconds=db_url.url_expires)
        time2 = datetime.now()
        print("--------", time1 < time2, "------------", time2)
        if time1 < time2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Link is dead.")
            query = delete(VipStorage).where(UrlStorage.secret_key == secret_key)
            await session.execute(query)
            await session.commit()

    db_url.short_url = url_from_suffix(db_url.short_url)
    return GetInfoAboutLinkResponse.from_orm(db_url)
