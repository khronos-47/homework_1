from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from fastapi.exceptions import HTTPException
from pydantic import UUID4, BaseModel, Field, HttpUrl, root_validator, validator
from starlette import status
from url_normalize import url_normalize


class MakeShorterRequest(BaseModel):
    url: HttpUrl = Field(title="URL to be shortened")

    @classmethod
    @validator("url", allow_reuse=True, pre=True)
    def normalize_link(cls, link):
        return url_normalize(link)


class MakeShorterResponse(BaseModel):
    short_url: HttpUrl = Field(title="Shortened URL")
    secret_key: UUID4

    class Config:
        from_attributes = True


class unit(str, Enum):
    DAYS = "DAYS"
    HOURS = "HOURS"
    MINUTES = "MINUTES"
    SECONDS = "SECONDS"


class VipUrlRequest(BaseModel):
    url: str
    vip_key: str
    time_to_live: Optional[int] = 10
    time_to_live_unit: Optional[unit] = unit.HOURS

    @validator("url", allow_reuse=True, pre=True)
    def normalize_link(cls, link):
        return url_normalize(link)

    @validator("time_to_live_unit")
    def validate_ttl_unit(cls, v):
        allowed_units = {"SECONDS", "MINUTES", "HOURS", "DAYS"}
        if v not in allowed_units:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ttl unit error",
            )
        return v

    @root_validator(pre=True)
    def validate_ttl(cls, values):

        ttl = values.get("time_to_live")
        ttl_unit = values.get("time_to_live_unit")
        if ttl_unit == None:
            ttl_unit = unit.HOURS
        if ttl and ttl_unit:
            if ttl_unit == "SECONDS" and ttl > 172800:  # 2 days in seconds
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ttl error",
                )
            if ttl_unit == "MINUTES" and ttl > 2880:  # 2 days in minutes
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ttl error",
                )
            if ttl_unit == "HOURS" and ttl > 48:  # 2 days in hours
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ttl error",
                )
            if ttl_unit == "DAYS" and ttl > 2:  # 2 days
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ttl error",
                )
        return values


class VipUrlResponse(BaseModel):
    short_url: HttpUrl = Field(title="Shortened URL")
    secret_key: UUID4

    class Config:
        from_attributes = True
