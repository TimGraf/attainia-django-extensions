#pylint:disable=W0622
""" Decorator for Nameko event handler """
from uuid import uuid4

from nameko.events import event_handler as nameko_event_handler

from cid import locals


def event_handler_decorator_with_cid(channel_name: str, event_name: str, *args, **kwargs):
    """ Wrap a Namkeo event handler """
    def decorator_wrapper(function):
        """ Wrapper function for the decorator """
        @nameko_event_handler(channel_name, event_name, *args, **kwargs)
        def wrapper(self, event_data):
            """ Function wrapper """
            # get the CID off of the event data and set it on the local thread
            locals.set_cid(event_data.pop("cid", str(uuid4())))

            return function(self, event_data)

        return wrapper

    return decorator_wrapper
