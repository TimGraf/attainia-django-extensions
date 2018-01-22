#pylint:disable=W0703
#pylint:disable=W0622
""" RPC Abstraction Wrapper """
import json
import logging
from uuid import uuid4

from nameko.events import EventDispatcher
from nameko.dependency_providers import Config

from cid import locals


"""
A mixin class for dispatching events and including a CID.
"""
class EventDispatchWithCidMixin(object):
    """
    Example usage:

        MyClass(EventDispatchWithCidMixin):
            ...

            # Dispatch event
            self.dispatch_event("user_created", {"email": email, "uuid": uuid})

    """
    logger = logging.getLogger(__name__)
    # Nameko Config is a simple dependency provider
    config = Config()
    # Nameko event dispatcher
    dispatch = EventDispatcher()

    def dispatch_event(self, event_name: str, event_data: dict):
        """ Dispatch event """
        self.logger.debug("Dispatching event: %s, event data: %s", event_name, json.dumps(event_data))

        # Get the correlation ID if it exists, otherwise create one
        cid = locals.get_cid() or str(uuid4())
        event_data["cid"] = cid

        self.dispatch(event_name, event_data)
