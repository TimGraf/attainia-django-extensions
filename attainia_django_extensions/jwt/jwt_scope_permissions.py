""" JWT Scope Permissions """
import inspect
import logging

from django.conf import settings

from rest_framework import permissions
from rest_framework.authentication import get_authorization_header

from ..rpc.rpc_mixin import RpcMixin


"""
    http://www.django-rest-framework.org/api-guide/permissions/#custom-permissions

    The Nameko RPC authorization service name and token validation method name are required
    to be in the Django settings as well.

        AUTH_SERVICE_NAME = "auth_service"
        VALIDATE_TOKEN_METHOD = "validate_token"

    Required permissions are defined in the settings as view class mapped to a resource.
    The actions are mapped to HTTP methods.

        VIEW_PERMISSIONS = {
            "SampleResourceViewSet": "example"
        }

    Example JWT with sample scopes.

        {
            "aud": "svcattainia",
            "iss": "svcattainiaauth_api",
            "iat": 1513269779,
            "exp": 1513273379,
            "sub": "a8a68e1f-4284-41e1-9f8b-70f7abc7247f",
            "name": "superuser@attainia.com",
            "org": "fc890cdc-e637-457d-805e-5495004f1654",
            "scope": "example:create example:read example:update example:delete"
        }

"""
class JwtScopePermission(permissions.BasePermission, RpcMixin):
    """ JWT Scope Permissions Class """
    logger = logging.getLogger(__name__)
    message = "Required scope not found."
    method_actions = {
        "POST": "create",
        "GET": "read",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
        "OPTIONS": "read",
        "HEAD": "read"
    }
    auth_service_name = settings.AUTH_SERVICE_NAME
    validate_token_method = settings.VALIDATE_TOKEN_METHOD

    def has_permission(self, request, view):
        self.logger.debug("JwtScopePermission.has_permission")

        try:
            token = get_authorization_header(request).decode().split()[1]
            self.logger.debug("Validating token: %s", token)

            token_resp = self.call_service_method(self.auth_service_name, self.validate_token_method, False, token)
            self.logger.debug("Token Response: %s", token_resp)

            return self._token_includes_scope(token_resp, view, request.method)

        except Exception as ex:
            self.logger.warning("Permissions failed with error %s", getattr(ex, 'message', repr(ex)))
            return False

    def _token_includes_scope(self, token_response, view, method):
        view_class = None
        scopes = token_response["scope"]

        if inspect.isclass(view):
            view_class = view.__name__
        else:
            view_class = view.__class__.__name__

        if "superuser" in scopes:
            self.logger.debug("Super user access, user ID: %s, view: %s", token_response["sub"], view_class)
            return True

        resource = settings.VIEW_PERMISSIONS.get(view_class, "example")
        action = self.method_actions.get(method)

        self.logger.debug("resource: %s", resource)
        self.logger.debug("action: %s", action)

        required_scope = resource + ":" + action

        self.logger.debug("JWT Scopes: %s", scopes)
        self.logger.debug("Required Scope: %s", required_scope)

        return required_scope in scopes
