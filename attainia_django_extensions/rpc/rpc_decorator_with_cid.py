from uuid import uuid4

from nameko.rpc import rpc as nameko_rpc

from cid import locals


def rpc_decorator_with_cid(function):
    """ Wrap a Namkeo RPC call """

    @nameko_rpc
    def wrapper(self, *args, **kwargs):
        """ Call wrapped function getting cid from RPC call """
        cid = kwargs.pop("jwt", str(uuid4()))

        locals.set_cid(cid)
        
        return function(self, *args, **kwargs)

    return wrapper
