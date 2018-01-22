#pylint:disable=W0622
""" RPC Abstraction Wrapper """
import logging
from uuid import uuid4

from nameko.dependency_providers import Config
from nameko.events import EventDispatcher
from nameko.standalone.rpc import ClusterRpcProxy

from cid import locals


"""
A mixin class for making RPC calls.
"""
class DjangoRpcWithCidMixin(object):
    """
    Example usage:

        MyClass(DjangoRpcWithCidMixin):
            ...

            # Make service RPC
            self.call_service_method("auth_publisher", "user_created", True, email, uuid)


    Requires Nameko Config, a simple dependency provider that gives services read-only access
    to configuration values at run time.

    """
    logger = logging.getLogger(__name__)
    # Nameko config dependency
    config = Config()
    # Nameko event dispatcher
    dispatch = EventDispatcher()

    def call_service_method(self, service_name: str, method_name: str, use_async: bool, *args, **kwargs):
        """ Call an RPC method from a service """
        self.logger.debug("Calling service: %s, method: %s", service_name, method_name)

        try:
            # Get the correlation ID if it exists, otherwise create one
            cid = locals.get_cid() or str(uuid4())

            with ClusterRpcProxy(self.config) as cluster_rpc:
                service = getattr(cluster_rpc, service_name)
                method = getattr(service, method_name)
                new_kwargs = {**kwargs, **{"cid": cid}}

                if use_async:
                    return method.call_async(cid, *args, **new_kwargs)
                else:
                    return method(cid, *args, **new_kwargs)

        except Exception as ex:
            self.logger.error("RPC call failed with error %s", getattr(ex, 'message', repr(ex)))
            raise ex
