from typing import Annotated
from fastapi import APIRouter, Depends, Path, status, HTTPException
from pydantic import UUID4

from store import services
from store.domains import Role
from store.repositories import Repository
from store.schemas import (
    ChangeItemModel,
    CreateItemModel,
    ErrorModel,
    GetItemModel,
    GetItemsModel,
    LoginModel,
)

router = APIRouter(prefix="/items", tags=["Товары"])


@router.get("", response_model=GetItemsModel)
def get_items() -> GetItemsModel:
    """Получение списка товаров

    Returns:
        GetItemsModel: список товаров
    """
    items = services.get_items(Repository.items())
    return GetItemsModel(
        items=[
            GetItemModel(
                id=item.id,
                name=item.name,
                description=item.description,
                price=item.price / 100,
            )
            for item in items
        ]
    )


@router.post(
    "",
    response_model=GetItemModel,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": GetItemModel},
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
    },
)
def create_item(
    item: Annotated[CreateItemModel, Depends()],
    credentials: Annotated[LoginModel, Depends()],
) -> (
    GetItemModel
):  # credentials – тело с логином и паролем. Обычно аутентификация выглядит сложнее, но для нашего случая пойдет и так.
    """Создание товара

    Args:
        item (CreateItemModel): данные нового товара
        credentials (LoginModel): учетные данные пользователя

    Raises:
        HTTPException: 401 если аутентификация не пройдена
        HTTPException: 403 если авторизация не пройдена

    Returns:
        GetItemModel: товар
    """

    services.authorize(credentials, Role.ADMIN)

    item = services.create_item(
        item.name,
        int(item.price * 100),
        Repository.items(),
        item.description,
    )
    return GetItemModel(
        id=item.id, name=item.name, description=item.description, price=item.price / 100
    )


@router.put(
    "/{item_id}",
    response_model=GetItemModel,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": GetItemModel},
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        404: {"model": ErrorModel},
    },
)
def change_item(
    item_id: Annotated[UUID4, Path()],
    data: Annotated[ChangeItemModel, Depends()],
    credentials: Annotated[LoginModel, Depends()],
):  # credentials – тело с логином и паролем. Обычно аутентификация выглядит сложнее, но для нашего случая пойдет и так.
    """Изменение товара

    Args:
        item_id (str): id товара
        data (ChangeItemModel): данные товара
        credentials (LoginModel): учетные данные пользователя

    Raises:
        HTTPException: 401 если аутентификация не пройдена
        HTTPException: 403 если авторизация не пройдена
        HTTPException: 404 если не найден товар
    """

    services.authorize(credentials, Role.MANAGER)

    try:
        item = services.change_item(
            str(item_id),
            Repository.items(),
            name=data.name,
            description=data.description,
            price=int(data.price * 100),
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="item not found"
        )

    return GetItemModel(
        id=item.id, name=item.name, description=item.description, price=item.price / 100
    )
