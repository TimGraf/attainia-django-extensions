#pylint:disable=W0703
#pylint:disable=W0622
""" RPC Abstraction Wrapper """
import json
import logging
from uuid import uuid4

from django.conf import settings
from django.utils.module_loading import import_string

from nameko.events import EventDispatcher
from nameko.dependency_providers import Config

from cid import locals


"""
A mixin class for making RPC calls.
"""
class RpcMixin(object):
    """
    Example usage:

        MyClass(RpcMixin):
            ...
    """
    logger = logging.getLogger(__name__)
    # Nameko Config is a simple dependency provider
    config = Config()
    # Nameko event dispatcher
    dispatch = EventDispatcher()

    def _get_connection_pool(self):
        """ Get a connection from the pool """
        # Connection pool for RPC cluster.
        conn_pool_provider_path = import_string(settings.RPC_CONNECTION_POOL_PROVIDER)
        return conn_pool_provider_path()

    def call_service_method(self, service_name: str, method_name: str, use_async: bool, *args):
        """ Call an RPC method from a service """
        self.logger.debug("Calling service: %s, method: %s", service_name, method_name)

        try:
            # Get the correlation ID if it exists, otherwise create one
            cid = locals.get_cid() or str(uuid4())

            with self._get_connection_pool().next() as rpc:
                service = getattr(rpc, service_name)
                method = getattr(service, method_name)

                if use_async:
                    return method.call_async(cid, *args)
                else:
                    return method(cid, *args)

        except Exception as ex:
            self.logger.error("RPC call failed with error %s", getattr(ex, 'message', repr(ex)))

            return None

    def dispatch_event(self, event_name: str, event_data: dict):
        """ Dispatch event """
        self.logger.debug("Dispatching event: %s, event data: %s", event_name, json.dumps(event_data))

        # Get the correlation ID if it exists, otherwise create one
        cid = locals.get_cid() or str(uuid4())
        event_data["cid"] = cid

        self.dispatch(event_name, event_data)
