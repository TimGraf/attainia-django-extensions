"""
Abstraction for Nameko RPC decorator to add the CID to local thread for logging.
"""
from uuid import uuid4

from nameko.rpc import rpc as nameko_rpc

from cid import locals


def rpc_decorator_with_cid(*args, **kwargs):
    """ Wrap a Namkeo RPC call """
    def decorator_wrapper(function):
        """ Wrapper function for the decorator """
        @nameko_rpc(*args, **kwargs)
        def wrapper(self, *args, **kwargs):
            """ Call wrapped function getting cid from RPC call """
            cid = kwargs.pop("cid", str(uuid4()))

            locals.set_cid(cid)

            return function(self, *args, **kwargs)

        return wrapper

    return decorator_wrapper
