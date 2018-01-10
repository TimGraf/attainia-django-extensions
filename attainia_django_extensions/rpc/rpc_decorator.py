#pylint:disable=W0622
""" Decorator for Nameko RPC """
import logging

from rest_framework.response import Response
from rest_framework import status

from nameko.rpc import rpc

from cid import locals

from . import rpc_errors


def rpc_decorator(function):
    """ Wrap a Namkeo RPC call """

    @rpc
    def wrapper(self, cid, *args, **kwargs):
        """ Call wrapped function getting cid from RPC call """
        locals.set_cid(cid)
        return function(self, *args, **kwargs)

    return wrapper

def handle_rpc_error(resp):
    logger = logging.getLogger(__name__)

    status_code = status.HTTP_200_OK

    if rpc_errors.OBJ_NOT_FOUND_KEY in resp[rpc_errors.ERRORS_KEY]:
        status_code = status.HTTP_404_NOT_FOUND
    elif rpc_errors.NOT_AUTHENTICATED_KEY in resp[rpc_errors.ERRORS_KEY]:
        status_code = status.HTTP_401_UNAUTHORIZED
    elif rpc_errors.NOT_AUTHORIZED_KEY in resp[rpc_errors.ERRORS_KEY]:
        status_code = status.HTTP_403_FORBIDDEN

    return status_code

def rpc_error_handler(function):
    """ Wrap RpcDrfViewSet methods to handle RPC errors and return appropriate HTTP response codes.

        Methods like: list, retrieve, update, create, and delete, which require potentially handling
        RPC errors and translating those into HTTP status codes.
    """

    def wrapper(self, *args, **kwargs):
        """ Call wrapped function """
        logger = logging.getLogger(__name__)

        try:
            status_code = status.HTTP_201_CREATED if function.__name__ == "create" else status.HTTP_200_OK
            resp = function(self, *args, **kwargs)

            if resp is not None:
                if rpc_errors.ERRORS_KEY in resp.keys():
                    status_code = handle_rpc_error(resp)

                if rpc_errors.VALIDATION_ERRORS_KEY in resp.keys():
                    status_code = status.HTTP_400_BAD_REQUEST

            logger.debug("Response: %s", repr(resp))

            return Response(resp, status=status_code)
        except Exception as ex:
            logger.error("Wrapped function call failed with error %s", getattr(ex, 'message', repr(ex)))
            return Response(None, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    return wrapper
