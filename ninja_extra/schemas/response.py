import sys
import traceback
from typing import Any, Callable, Generic, List, Optional, Type, TypeVar, cast

from django.db.models import Model
from ninja import Schema
from ninja.constants import NOT_SET
from pydantic.generics import GenericModel
from pydantic.main import BaseModel
from pydantic.networks import AnyHttpUrl

from ninja_extra.generic import GenericType

T = TypeVar("T")


class BasePaginatedResponseSchema(Schema):
    count: int
    next: Optional[AnyHttpUrl]
    previous: Optional[AnyHttpUrl]
    results: List[Any]


class BaseNinjaResponseSchema(Schema):
    count: int
    items: List[Any]


class PaginatedResponseSchema(GenericType):
    def get_generic_type(
        self, wrap_type: Any
    ) -> Type[BasePaginatedResponseSchema]:  # pragma: no cover
        class ListResponseSchema(BasePaginatedResponseSchema):
            results: List[wrap_type]  # type: ignore

        ListResponseSchema.__name__ = (
            f"{self.__class__.__name__}[{str(wrap_type.__name__).capitalize()}]"
        )
        return ListResponseSchema


class NinjaPaginationResponseSchema(GenericType):
    def get_generic_type(
        self, wrap_type: Any
    ) -> Type[BaseNinjaResponseSchema]:  # pragma: no cover
        class ListNinjaResponseSchema(BaseNinjaResponseSchema):
            items: List[wrap_type]  # type: ignore

        ListNinjaResponseSchema.__name__ = (
            f"{self.__class__.__name__}[{str(wrap_type.__name__).capitalize()}]"
        )
        return ListNinjaResponseSchema


if sys.version_info >= (3, 8):  # pragma: no cover

    class PaginatedResponseSchema(
        GenericModel, Generic[T], BasePaginatedResponseSchema
    ):
        results: List[T]

    class NinjaPaginationResponseSchema(
        GenericModel, Generic[T], BaseNinjaResponseSchema
    ):
        items: List[T]


class RouteParameter(BaseModel):
    path: str
    methods: List[str]
    auth: Any = NOT_SET
    response: Any = NOT_SET
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    deprecated: Optional[bool] = None
    by_alias: bool = False
    exclude_unset: bool = False
    exclude_defaults: bool = False
    exclude_none: bool = False
    url_name: Optional[str] = None
    include_in_schema: bool = True


class ModelControllerSchema:
    dict: Callable
    config: BaseModel.Config

    def perform_create(self, **kwargs: Any) -> Any:
        data = self.dict(by_alias=True)
        data.update(kwargs)
        model = cast(Model, self.config.model)
        try:
            instance = model._default_manager.create(**data)
            return instance
        except TypeError:
            tb = traceback.format_exc()
            msg = (
                "Got a `TypeError` when calling `%s.%s.perform_create()`. "
                "This may be because you have a writable field on the "
                "serializer class that is not a valid argument to "
                "`%s.%s.create()`. You may need to make the field "
                "read-only, or override the %s.perform_create() method to handle "
                "this correctly.\nOriginal exception was:\n %s"
                % (
                    model.__name__,
                    model._default_manager.name,
                    model.__name__,
                    model._default_manager.name,
                    self.__class__.__name__,
                    tb,
                )
            )
            raise TypeError(msg)

    def perform_update(self, instance: Model, **kwargs: Any) -> Any:
        data = self.dict(exclude_none=True)
        data.update(kwargs)
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def perform_patch(self, instance: Model, **kwargs: Any) -> Any:
        return self.perform_update(instance=instance, **kwargs)
