""" Django ORM Search Nameko Dependency Provider """
import operator
from collections import OrderedDict
from functools import reduce

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query import QuerySet

from nameko.extensions import DependencyProvider

from . import rpc_errors
from .rpc_view_adapter import RpcViewAdapter


def querydict_to_dict(querydict):
    return {k: v[0] if len(v) == 1 else v for k, v in querydict.lists()}

class DjangoSearchProvider(DependencyProvider):

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
        return DjangoSearch(self.queryset, self.serializer_class, self.search_fields)


class DjangoSearch(RpcViewAdapter):
    """
    Provides common DRF ViewSet-like abstractions for interacting with models
    and serializers via RPC.
    """
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

    def get_search_fields(self):
        return self.search_fields

    def construct_search(self, field_name):
        lookup = self.search_lookup_prefixes.get(field_name[0])
        if lookup:
            field_name = field_name[1:]
        else:
            lookup = "icontains"
        return LOOKUP_SEP.join([field_name, lookup])

    def search_queryset(self, queryset, search_terms):
        search_fields = self.get_search_fields()
        search_terms = search_terms.replace(",", " ").split()

        if not search_fields or not search_terms:
            return queryset

        orm_lookups = [
            self.construct_search(search_field)
            for search_field in search_fields
        ]

        base = queryset
        conditions = []
        for search_term in search_terms:
            queries = [
                Q(**{orm_lookup: search_term})
                for orm_lookup in orm_lookups
            ]
            conditions.append(reduce(operator.or_, queries))
        queryset = queryset.filter(reduce(operator.and_, conditions))

        return queryset

    @RpcViewAdapter.auth
    def search(self, *args, **kwargs):
        page_num = int(kwargs.pop("page", 1))
        page_size = int(kwargs.pop("page_size", settings.PAGINATION["PAGE_SIZE"]))

        if page_size > settings.PAGINATION["MAX_PAGE_SIZE"]:
            page_size = settings.PAGINATION["MAX_PAGE_SIZE"]

        search_terms = kwargs.pop("query", "")

        if not search_terms:
            return {rpc_errors.ERRORS_KEY: {rpc_errors.MISSING_SEARCH_PARAM_KEY: rpc_errors.MISSING_SEARCH_PARAM_VALUE}}

        queryset = self.search_queryset(self.queryset, search_terms)
        page = self.paginate_queryset(queryset, page_num, page_size)
        if page is not None:
            serializer = self.get_serializer(page, many=True, *args, **kwargs)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, *args, **kwargs)
        return serializer.data
