from typing import Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: T


def success_response(data: T, message: str = "success") -> ApiResponse[T]:
    return ApiResponse[T](
        code=0,
        message=message,
        data=data,
    )
