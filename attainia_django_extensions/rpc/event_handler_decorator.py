#pylint:disable=W0622
""" Decorator for Nameko event handler """
from nameko.events import event_handler

from cid import locals


def event_handler_decorator(channel_name: str, event_name: str):
    """ Wrap a namkeo event handler """
    def decorator_wrapper(function):
        """ Wrapper function for the decorator """
        @event_handler(channel_name, event_name)
        def wrapper(self, event_data):
            """ Function wrapper """
            # get the CID off of the event data and set it on the local thread
            locals.set_cid(event_data.pop("cid"))

            return function(self, event_data)

        return wrapper

    return decorator_wrapper
