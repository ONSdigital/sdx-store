import pika

import settings


class Publishers():
    """Persists the QueuePublisher objects instantiated for CTP, CORA and
       CS endpoints.

    Args:
        logger (Logging.logger): Variable holding a logger object.

    Attributes:
        cora (QueuePublisher): Cora queue QueuePublisher object.
        ctp (QueuePublisher): CTP queue QueuePublisher object.
        cs (QueuePublisher): CS queue QueuePublisher object.
        """

    def __init__(self, logger):
        self.logger = logger

        self.cs = QueuePublisher(self.logger,
                                 settings.RABBIT_URLS,
                                 settings.RABBIT_CS_QUEUE)

        self.ctp = QueuePublisher(self.logger,
                                  settings.RABBIT_URLS,
                                  settings.RABBIT_CS_QUEUE)

        self.cora = QueuePublisher(self.logger,
                                   settings.RABBIT_URLS,
                                   settings.RABBIT_CORA_QUEUE)


class QueuePublisher(object):

    def __init__(self, logger, urls, queue):
        self._logger = logger
        self._urls = urls
        self._queue = queue
        self._connection = None
        self._channel = None

    def _connect(self):
        self._logger.debug("Connecting to queue", queue=self._queue)
        for url in self._urls:
            try:
                self._connection = pika.BlockingConnection(pika.URLParameters(url))
                self._channel = self._connection.channel()
                self._channel.queue_declare(queue=self._queue, durable=False)
                self._logger.debug("Connected to queue")
                return True

            except pika.exceptions.AMQPConnectionError as e:
                self._logger.error("Unable to connect to queue", exception=repr(e))
                continue

        return False

    def _disconnect(self):
        try:
            self._connection.close()
            self._logger.debug("Disconnected from queue")

        except Exception as e:
            self._logger.error("Unable to close connection", exception=repr(e))

    def _publish(self, message):
        try:
            self._channel.basic_publish(exchange='', routing_key=self._queue, body=message)
            self._logger.debug("Published message")
            return True

        except Exception as e:
            self._logger.error("Unable to publish message", exception=repr(e))
            return False

    def publish_message(self, message):
        self._logger.debug("Sending message")
        if not self._connect():
            return False

        if not self._publish(message):
            return False

        self._disconnect()
        return True
