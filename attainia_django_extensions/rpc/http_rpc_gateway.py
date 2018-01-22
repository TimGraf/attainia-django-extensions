import operator
from collections import OrderedDict
from functools import reduce

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query import QuerySet
from rest_framework import viewsets
from rest_framework.authentication import get_authorization_header
from rest_framework.decorators import list_route

from . import rpc_errors
from .django_rpc_with_cid_mixin import DjangoRpcWithCidMixin
from .rpc_view import RpcView
from .rpc_http_error_marshaller import rpc_http_error_marshaller


def querydict_to_dict(querydict):
    return {k: v[0] if len(v) == 1 else v for k, v in querydict.lists()}


class HttpRPCGateway(viewsets.ViewSet, DjangoRpcWithCidMixin):
    """
    A DRF based ViewSet base class that provides a CRUDL HTTP API gateway
    to interact with Nameko RPC calls.
    """
    rpc_service_name = None

    def _getJwt(self, request):
        jwt = None

        try:
            jwt = get_authorization_header(request).decode().split()[1]
        except Exception as ex:
            jwt = None

        return jwt


    def get_rpc_service_name(self):
        assert self.rpc_service_name is not None, (
            "'%s' should either include a `rpc_service_name` attribute, "
            "or override the `get_rpc_service_name()` method."
            % self.__class__.__name__
        )

        rpc_service_name = self.rpc_service_name
        return rpc_service_name

    @list_route(methods=["get"], url_path="search")
    @rpc_http_error_marshaller
    def search(self, request, *args, **kwargs):
        jwt = self._getJwt(request)
        params = querydict_to_dict(request.query_params)

        return self.call_service_method(
            self.get_rpc_service_name(),
            "search",
            False,
            **{**{"jwt": jwt}, **params},
        )

    @rpc_http_error_marshaller
    def list(self, request, *args, **kwargs):
        jwt = self._getJwt(request)
        params = querydict_to_dict(request.query_params)

        return self.call_service_method(
            self.get_rpc_service_name(),
            "list",
            False,
            **{**{"jwt": jwt}, **params},
        )

    @rpc_http_error_marshaller
    def retrieve(self, request, pk, *args, **kwargs):
        jwt = self._getJwt(request)
        params = querydict_to_dict(request.query_params)

        return self.call_service_method(
            self.get_rpc_service_name(),
            "retrieve",
            False,
            **{**{"jwt": jwt}, **{"pk": pk}, **params},
        )

    @rpc_http_error_marshaller
    def create(self, request, *args, **kwargs):
        jwt = self._getJwt(request)

        return self.call_service_method(
            self.get_rpc_service_name(),
            "create",
            False,
            **{**{"jwt": jwt}, **request.data}
        )

    @rpc_http_error_marshaller
    def update(self, request, pk, *args, **kwargs):
        jwt = self._getJwt(request)
        request_data = request.data
        request_data["partial"] = kwargs.pop("partial", False)

        return self.call_service_method(
            self.get_rpc_service_name(),
            "update",
            False,
            **{**{"jwt": jwt}, **{"pk": pk}, **request_data}
        )

    def partial_update(self, request, pk, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, pk, *args, **kwargs)
