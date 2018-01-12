"""
Provides an RPCView class that is the base of all views in the RPC framework.
"""
import logging

from rest_framework import exceptions
from rest_framework.settings import api_settings

from . import rpc_errors


class RpcView(object):
    logger = logging.getLogger(__name__)
    # The following policies may be set  per-view.
    authentication_classes = ()
    permission_classes = ()

    # Allow dependency injection of other settings to make testing easier.
    settings = api_settings

    # Creating a mock request object to keep permissions and authorization classes interchangable with DRF.
    class Request:
        user = None
        auth = None
        method = None
        META = None

    request = Request()


    def _put_jwt_on_auth_header(self, kwargs):
        jwt = kwargs.pop("jwt", None)
        self.request.META = {
            "HTTP_AUTHORIZATION": "Bearer {0}".format(jwt).encode('UTF-8')
        }

    def _set_request_method(self, function_name):
        method = {
            "list": "GET",
            "retrieve": "GET",
            "create": "POST",
            "update": "PUT",
            "partial_update": "PATCH"
        }.get(function_name, "GET")
        self.request.method = method

    @classmethod
    def auth(cls, function):
        """ Authorization and Authentication decorator """
        def wrapper(self, *args, **kwargs):
            """ Decorator wrapping function """
            self._put_jwt_on_auth_header(kwargs)
            self._set_request_method(function.__name__)
            # Perform the authentication and authorization
            auth_res = self.perform_authentication()
            perm_res = self.check_permissions()

            if auth_res is not None:
                return auth_res

            if perm_res is not None:
                return perm_res

            return function(self, *args, **kwargs)

        return wrapper


    # Implementation borrowed from https://github.com/encode/django-rest-framework/blob/master/rest_framework/views.py
    def get_authenticators(self):
        """
        Instantiates and returns the list of authenticators that this view can use.
        """
        return [auth() for auth in self.authentication_classes]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permission_classes]

    # Modified from original since authentication happens on the request object in DRF.
    def perform_authentication(self):
        """
        Attempt to authenticate the request using each authentication instance
        in turn.

        Perform authentication on the incoming request.
        Note that if you override this and simply 'pass', then authentication
        will instead be performed lazily, the first time either
        `request.user` or `request.auth` is accessed.
        """
        for authenticator in self.get_authenticators():
            try:
                user_auth_tuple = authenticator.authenticate(self.request)
                self.request.user, self.request.auth = user_auth_tuple
            except Exception as ex:
                self.logger.warning("Authenticator failed with error %s", getattr(ex, 'message', repr(ex)))
                return {rpc_errors.ERRORS_KEY: {rpc_errors.NOT_AUTHENTICATED_KEY: rpc_errors.NOT_AUTHENTICATED_VALUE}}

            return None

        return None

    def check_permissions(self):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_permission(self.request, self):
                self.logger.warning("Permissions check failed.")
                return {rpc_errors.ERRORS_KEY: {rpc_errors.NOT_AUTHORIZED_KEY: rpc_errors.NOT_AUTHORIZED_VALUE}}

        return None
