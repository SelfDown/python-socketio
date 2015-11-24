import json
import pickle

import six
try:
    import redis
except ImportError:
    redis = None

from .pubsub_manager import PubSubManager


class RedisManager(PubSubManager):
    """Redis based client manager.

    This class implements a Redis backend for event sharing across multiple
    processes. Only kept here as one more example of how to build a custom
    backend, since the kombu backend is perfectly adequate to support a Redis
    message queue.

    To use a Redis backend, initialize the :class:`Server` instance as
    follows::

        url = 'redis://hostname:port/0'
        server = socketio.Server(client_manager=socketio.RedisManager(url))

    :param url: The connection URL for the Redis server.
    :param channel: The channel name on which the server sends and receives
                    notifications. Must be the same in all the servers.
    """
    name = 'redis'

    def __init__(self, url='redis://localhost:6379/0', channel='socketio'):
        if redis is None:
            raise RuntimeError('Redis package is not installed '
                               '(Run "pip install redis" in your '
                               'virtualenv).')
        self.redis = redis.Redis.from_url(url)
        self.pubsub = self.redis.pubsub()
        super(RedisManager, self).__init__(channel=channel)

    def _publish(self, data):
        return self.redis.publish(self.channel, pickle.dumps(data))

    def _listen(self):
        channel = self.channel.encode('utf-8')
        self.pubsub.subscribe(self.channel)
        for message in self.pubsub.listen():
            if message['channel'] == channel and \
                    message['type'] == 'message' and 'data' in message:
                data = None
                if isinstance(message['data'], six.binary_type):
                    try:
                        data = pickle.loads(message['data'])
                    except pickle.PickleError:
                        pass
                if data is None:
                    data = json.loads(message['data'])
                yield data
        self.pubsub.unsubscribe(self.channel)
