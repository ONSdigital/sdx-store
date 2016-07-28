import pika
import settings


class StoreQueue(object):

    def __init__(self, logger):
        self._logger = logger
        self._connection = None
        self._channel = None

    def __connect(self):
        self._logger.debug("Connecting to queue")
        for url in settings.RABBIT_URLS:
            try:
                self._connection = pika.BlockingConnection(pika.URLParameters(url))
                self._channel = self._connection.channel()
                self._channel.queue_declare(queue=settings.RABBIT_QUEUE)
                self._logger.debug("Connected to queue", url=url)
                return True

            except pika.exceptions.AMQPConnectionError as e:
                self._logger.error("Unable to connect to queue", exception=repr(e), url=url)
                continue

        return False

    def __disconnect(self):
        try:
            self._connection.close()
            self._logger.debug("Disconnected from queue")

        except Exception as e:
            self._logger.error("Unable to close connection", exception=repr(e))

    def __publish(self, notification):
        try:
            self._channel.basic_publish(exchange='', routing_key=settings.RABBIT_QUEUE, body=notification)
            self._logger.debug("Published notification")
            return True

        except Exception as e:
            self._logger.error("Unable to publish notification", exception=repr(e))
            return False

    def send(self, notification):
        self._logger.debug("Sending notification")
        if not self.__connect():
            return False

        if not self.__publish(notification):
            return False

        self.__disconnect()
        return True
