#pylint:disable=W0622
""" Decorator for Nameko RPC """
from nameko.rpc import rpc

from cid import locals


def rpc_decorator(function):
    """ Wrap a Namkeo RPC call """

    @rpc
    def wrapper(self, cid, *args):
        """ Call wrapped function getting cid from RPC call """
        locals.set_cid(cid)
        return function(self, *args)

    return wrapper
