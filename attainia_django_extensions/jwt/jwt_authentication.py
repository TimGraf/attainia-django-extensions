""" JWT Authentication """
import logging

from rest_framework import authentication, exceptions
from rest_framework.authentication import get_authorization_header

from ..rpc.rpc_mixin import RpcMixin


"""
http://www.django-rest-framework.org/api-guide/authentication/#custom-authentication

"""
class JwtAuthentication(authentication.BaseAuthentication, RpcMixin):
    """ JWT Authentication Class """
    logger = logging.getLogger(__name__)

    def authenticate(self, request):
        self.logger.debug("JWTAuthentication.authenticate")

        try:
            token: str = get_authorization_header(request).decode().split()[1]
            self.logger.debug("Validating token: %s", token)

            token_resp = self.call_service_method("auth_service", "validate_token", False, token)
            self.logger.debug("Token Response: %s", token_resp)

            if token_resp:
                return (token_resp, token)
            else:
                raise exceptions.AuthenticationFailed()

        except Exception as ex:
            self.logger.warning("Authentication failed with error %s", getattr(ex, 'message', repr(ex)))
            raise exceptions.AuthenticationFailed()
