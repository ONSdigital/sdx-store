import pika


class QueuePublisher(object):

    def __init__(self, logger, urls, queue):
        self._logger = logger
        self._urls = urls
        self._queue = queue
        self._connection = None
        self._channel = None

    def _connect(self):
        self._logger.debug("Connecting to queue")
        for url in self._urls:
            try:
                self._connection = pika.BlockingConnection(pika.URLParameters(url))
                self._channel = self._connection.channel()
                self._channel.queue_declare(queue=self._queue)
                self._logger.debug("Connected to queue", url=url)
                return True

            except pika.exceptions.AMQPConnectionError as e:
                self._logger.error("Unable to connect to queue", exception=repr(e), url=url)
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
