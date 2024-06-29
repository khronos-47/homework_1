from fastapi import APIRouter, Depends, Path
from fastapi.responses import Response
from pydantic import UUID4
from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from shortener.db.connection import get_session
from shortener.db.models import UrlStorage, VipStorage


api_router = APIRouter(tags=["Url"])


@api_router.delete(
    "/admin/{secret_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_link(
    secret_key: UUID4 = Path(...),
    session: AsyncSession = Depends(get_session),
):
    exist_query = select(exists().where(VipStorage.secret_key == secret_key))
    exist = await session.scalar(exist_query)
    if not exist:
        query = delete(UrlStorage).where(UrlStorage.secret_key == secret_key)
    else:
        query = delete(VipStorage).where(VipStorage.secret_key == secret_key)
    print("-------", query)
    await session.execute(query)
    await session.commit()
