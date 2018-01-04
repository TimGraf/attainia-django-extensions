"""
Provides an RPCView class that is the base of all views in the RPC framework.
"""
from rest_framework import exceptions
from rest_framework.settings import api_settings


class APIView(object):

    # Auth errors
    ERRORS_KEY = "errors"
    NOT_AUTHENTICATED = "not_authenticated"
    NOT_AUTHORIZED = "not_authorized"

    # The following policies may be set  per-view.
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES

    # Allow dependency injection of other settings to make testing easier.
    settings = api_settings

    # Creating a mock request object to keep permissions class and authorization class interchangable with DRF.
    request = {}


    @classmethod
    def auth(cls, function):
        """ Authorization and Authentication decorator """
        def wrapper(self, *args, **kwargs):
            """ Decorator wrapping function """
            auth_res = self.perform_authentication()
            perm_res = self.check_permissions()

            if auth_res:
                return auth_res

            if perm_res:
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
        for authenticator in self.authentication_classes:
            try:
                user_auth_tuple = authenticator.authenticate(self.request)
            except exceptions.APIException:
                return {self.ERRORS_KEY, self.NOT_AUTHENTICATED}

            if user_auth_tuple is not None:
                self.request.user, self.request.auth = user_auth_tuple
                return

        return {self.ERRORS_KEY, self.NOT_AUTHENTICATED}

    def check_permissions(self):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_permission(self.request, self):
                return {self.ERRORS_KEY, self.NOT_AUTHORIZED}

        return
