""" Django data access Nameko dependency provider """
import operator
from collections import OrderedDict
from functools import reduce

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP

from nameko.extensions import DependencyProvider

from . import rpc_errors
from .rpc_view_adapter import RpcViewAdapter


def querydict_to_dict(querydict):
    return {k: v[0] if len(v) == 1 else v for k, v in querydict.lists()}


class DjangoDataAccessProvider(DependencyProvider):
    queryset = None
    serializer_class = None
    search_fields = []

    def setup(self):

        if self.container.get_queryset:
            self.queryset = self.container.get_queryset()
        elif self.container.queryset:
            self.queryset = self.container.queryset
        else:
            raise Exception("")

        if self.container.get_serializer_class:
            self.serializer_class = self.container.get_serializer_class()
        elif self.container.serializer_class:
            self.serializer_class = self.container.serializer_class
        else:
            raise Exception("")

        if self.container.search_fields:
            self.search_fields

    def get_dependency(self, worker_ctx):
        return DjangoDataAccess(self.queryset, self.serializer_class, self.search_fields)


class DjangoDataAccess(RpcViewAdapter):
    """
    Provides common DRF ViewSet-like abstractions for interacting with models
    and serializers via RPC.
    """
    lookup_field = "pk"
    lookup_kwarg = None
    search_lookup_prefixes = {
        "^": "istartswith",
        "=": "iexact",
        "@": "search",
        "$": "iregex",
    }

    def __init__(self, queryset, serializer_class, search_fields):
        self.queryset = queryset
        self.serializer_class = serializer_class
        self.search_fields = search_fields

    def get_object(self, **kwargs):
        queryset = self.queryset

        # Perform the lookup filtering.
        lookup_kwarg = self.lookup_kwarg or self.lookup_field

        assert lookup_kwarg in kwargs, (
            'Expected a keyword argument '
            'named "%s". Fix your RPC call, or set the `.lookup_field` '
            'attribute on the service correctly.' %
            (lookup_kwarg,)
        )

        filter_kwargs = {self.lookup_field: kwargs[lookup_kwarg]}

        obj = queryset.get(**filter_kwargs)
        return obj

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)

    def paginate_queryset(self, queryset, page_num, page_size):
        self.page_num = int(page_num)
        self.page_size = int(page_size)
        paginator = Paginator(queryset, self.page_size)
        self.page = paginator.page(self.page_num)
        return self.page

    def get_paginated_response(self, data):
        return OrderedDict([
            ("results", data),
            ("meta", {
                "total_results": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "page": self.page_num,
                "page_size": self.page_size,
            })
        ])

    @RpcViewAdapter.auth
    def create(self, *args, **kwargs):
        serializer = self.get_serializer(data=kwargs)

        if not serializer.is_valid():
            return {rpc_errors.VALIDATION_ERRORS_KEY: serializer.errors}

        serializer.save()
        return serializer.data

    @RpcViewAdapter.auth
    def list(self, *args, **kwargs):
        page_num = int(kwargs.pop("page", 1))
        page_size = int(kwargs.pop("page_size", settings.PAGINATION["PAGE_SIZE"]))

        if page_size > settings.PAGINATION["MAX_PAGE_SIZE"]:
            page_size = settings.PAGINATION["MAX_PAGE_SIZE"]

        page = self.paginate_queryset(self.queryset, page_num, page_size)
        if page is not None:
            serializer = self.get_serializer(page, many=True, *args, **kwargs)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(self.queryset, many=True, *args, **kwargs)
        return serializer.data

    @RpcViewAdapter.auth
    def retrieve(self, *args, **kwargs):
        try:
            instance = self.get_object(**kwargs)
        except ObjectDoesNotExist:
            return {rpc_errors.ERRORS_KEY: {rpc_errors.OBJ_NOT_FOUND_KEY: rpc_errors.OBJ_NOT_FOUND_ERROR_VALUE}}

        serializer = self.get_serializer(instance)
        return serializer.data

    @RpcViewAdapter.auth
    def update(self, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        try:
            instance = self.get_object(**kwargs)
        except ObjectDoesNotExist:
            return {rpc_errors.ERRORS_KEY: {rpc_errors.OBJ_NOT_FOUND_KEY: rpc_errors.OBJ_NOT_FOUND_ERROR_VALUE}}

        serializer = self.get_serializer(instance, data=kwargs, partial=partial)

        if not serializer.is_valid():
            return {rpc_errors.VALIDATION_ERRORS_KEY: serializer.errors}

        serializer.save()
        return serializer.data

    @RpcViewAdapter.auth
    def delete(self, *args, **kwargs):
        try:
            instance = self.get_object(**kwargs)
        except ObjectDoesNotExist:
            return {rpc_errors.ERRORS_KEY: {rpc_errors.OBJ_NOT_FOUND_KEY: rpc_errors.OBJ_NOT_FOUND_ERROR_VALUE}}

        instance_id = instance.id
        instance.delete()
        return {"id": str(instance_id)}
