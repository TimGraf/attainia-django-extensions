""" JWT Scope Permissions """
import inspect
import logging

from django.conf import settings

from rest_framework import permissions, request
from rest_framework.authentication import get_authorization_header

from ..rpc.rpc_mixin import RpcMixin


"""
    http://www.django-rest-framework.org/api-guide/permissions/#custom-permissions
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

    def has_permission(self, request, view):
        self.logger.debug("JwtScopePermission.has_permission")

        try:
            token: str = get_authorization_header(request).decode().split()[1]
            self.logger.debug("Validating token: %s", token)

            token_resp = self.call_service_method("auth_service", "validate_token", False, token)
            self.logger.debug("Token Response: %s", token_resp)

            if self._token_includes_scope(token_resp, view, request.method):
                return True
            else:
                return False

        except Exception as ex:
            self.logger.warning("Permissions failed with error %s", getattr(ex, 'message', repr(ex)))
            return False

    def _token_includes_scope(self, token_response, view, method):
        view_class = None
        scopes = token_response["scopes"]

        if inspect.isclass(view):
            view_class = view.__name__
        else:
            view_class = view.__class__.__name__

        resource = settings.VIEW_PERMISSIONS.get(view_class, "example")
        action = self.method_actions.get(method)

        self.logger.debug("resource: %s", resource)
        self.logger.debug("action: %s", action)

        required_scope = resource + ":" + action

        self.logger.debug("JWT Scopes: %s", scopes)
        self.logger.debug("Required Scope: %s", required_scope)

        return required_scope in scopes
