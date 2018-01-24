""" RPC  """
import logging
from uuid import uuid4

from nameko.extensions import DependencyProvider
from nameko.standalone.rpc import ClusterRpcProxy

from cid import locals


"""
RPC dependency provider with CID
"""
class RpcWithCidProvider(DependencyProvider):
    """
    Example usage:

        MyService():
            ...
            rpc_provider = RpcWithCidProvider()

            # Make service RPC
            rpc_provider.call_service_method("auth_publisher", "user_created", True, email, uuid)


    Requires Nameko Config, a simple dependency provider that gives services read-only access
    to configuration values at run time.

    """
    config = None

    def setup(self):
        self.config = self.container.config

    def get_dependency(self, worker_ctx):
        return RpcWithCid(self.config)


"""
A mixin class for making RPC calls.
"""
class RpcWithCid():
    """ RPC abstraction with CID """
    logger = logging.getLogger(__name__)
    config = None

    def __init__(self, config):
        self.config = config

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
                    return method.call_async(*args, **new_kwargs)
                else:
                    return method(*args, **new_kwargs)

        except Exception as ex:
            self.logger.error("RPC call failed with error %s", getattr(ex, 'message', repr(ex)))
            raise ex
