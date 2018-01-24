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


class DjangoSearch(RpcViewAdapter):
    """
    Provides common DRF ViewSet-like abstractions for interacting with models
    and serializers via RPC.
    """
    queryset = None
    serializer_class = None
    lookup_field = "pk"
    lookup_kwarg = None
    search_fields = None
    search_lookup_prefixes = {
        "^": "istartswith",
        "=": "iexact",
        "@": "search",
        "$": "iregex",
    }

    def get_queryset(self):
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method."
            % self.__class__.__name__
        )

        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            # Ensure queryset is re-evaluated on each request.
            queryset = queryset.all()
        return queryset

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

    def get_serializer_class(self):
        assert self.serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, "
            "or override the `get_serializer_class()` method."
            % self.__class__.__name__
        )

        return self.serializer_class

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

        queryset = self.search_queryset(self.get_queryset(), search_terms)
        page = self.paginate_queryset(queryset, page_num, page_size)
        if page is not None:
            serializer = self.get_serializer(page, many=True, *args, **kwargs)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, *args, **kwargs)
        return serializer.data
