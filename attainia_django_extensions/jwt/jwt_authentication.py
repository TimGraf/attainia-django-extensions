""" JWT Authentication """
import logging

from django.conf import settings

from rest_framework import authentication, exceptions
from rest_framework.authentication import get_authorization_header

from ..rpc.rpc_mixin import RpcMixin


"""
    http://www.django-rest-framework.org/api-guide/authentication/#custom-authentication

    The Nameko RPC authorization service name and token validation method name are required
    to be in the Django settings as well.

        AUTH_SERVICE_NAME = "auth_service"
        VALIDATE_TOKEN_METHOD = "validate_token"

"""
class JwtAuthentication(authentication.BaseAuthentication, RpcMixin):
    """ JWT Authentication Class """
    logger = logging.getLogger(__name__)
    auth_service_name = settings.AUTH_SERVICE_NAME
    validate_token_method = settings.VALIDATE_TOKEN_METHOD

    def authenticate(self, request):
        self.logger.debug("JWTAuthentication.authenticate")

        try:
            token: str = get_authorization_header(request).decode().split()[1]
            self.logger.debug("Validating token: %s", token)

            token_resp = self.call_service_method(self.auth_service_name, self.validate_token_method, False, token)
            self.logger.debug("Token Response: %s", token_resp)

            request.user = {
                "id": token_resp["sub"],
                "name": token_resp["name"],
                "org": token_resp["org"]
            }

            if token_resp:
                return (token_resp, token)
            else:
                raise exceptions.AuthenticationFailed()

        except Exception as ex:
            self.logger.warning("Authentication failed with error %s", getattr(ex, 'message', repr(ex)))
            raise exceptions.AuthenticationFailed()
