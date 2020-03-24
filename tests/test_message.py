import datetime
import random
import time
import unittest
import uuid

from pamqp import body, commands, constants, header

from aiorabbit import message


class TestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.exchange = str(uuid.uuid4())
        self.routing_key = str(uuid.uuid4())
        self.app_id = str(uuid.uuid4())
        self.content_encoding = str(uuid.uuid4())
        self.content_type = str(uuid.uuid4())
        self.correlation_id = str(uuid.uuid4())
        self.delivery_mode = random.randint(1, 2)
        self.expiration = str(int(time.time()) + random.randint(60, 300))
        self.headers = {str(uuid.uuid4()): str(uuid.uuid4())}
        self.message_id = str(uuid.uuid4())
        self.message_type = str(uuid.uuid4())
        self.priority = random.randint(0, 255)
        self.reply_to = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now()
        self.user_id = str(uuid.uuid4())
        self.body = b'-'.join(
            [str(uuid.uuid4()).encode('latin-1')
             for _offset in range(0, random.randint(1, 100))])

        self.message = message.Message(self.get_method())
        self.message.header = header.ContentHeader(
            0, len(self.body),
            commands.Basic.Properties(
                app_id=self.app_id,
                content_encoding=self.content_encoding,
                content_type=self.content_type,
                correlation_id=self.correlation_id,
                delivery_mode=self.delivery_mode,
                expiration=self.expiration,
                headers=self.headers,
                message_id=self.message_id,
                message_type=self.message_type,
                priority=self.priority,
                reply_to=self.reply_to,
                timestamp=self.timestamp,
                user_id=self.user_id))

        value = bytes(self.body)
        while value:
            self.message.body_frames.append(
                body.ContentBody(value[:constants.FRAME_MAX_SIZE]))
            value = value[constants.FRAME_MAX_SIZE:]

    def get_method(self):
        raise NotImplementedError

    def compare_message(self):
        for attribute in [
                'exchange', 'routing_key', 'app_id', 'content_encoding',
                'content_type', 'correlation_id', 'delivery_mode',
                'expiration', 'headers', 'message_id', 'message_type',
                'priority', 'reply_to', 'timestamp', 'user_id', 'body']:
            expectation = getattr(self, attribute)
            value = getattr(self.message, attribute)
            if isinstance(expectation, dict):
                self.assertDictEqual(value, expectation)
            else:
                self.assertEqual(value, expectation)
        self.assertEqual(bytes(self.message), self.body)
        self.assertEqual(len(self.message), len(self.body))
        self.assertTrue(self.message.is_complete)


class BasicDeliverTestCase(TestCase):

    def setUp(self) -> None:
        self.consumer_tag = uuid.uuid4().hex
        self.delivery_tag = random.randint(0, 100000000)
        self.redelivered = bool(random.randint(0, 1))
        super().setUp()

    def get_method(self):
        return commands.Basic.Deliver(
            self.consumer_tag, self.delivery_tag, self.redelivered,
            self.exchange, self.routing_key)

    def test_properties(self):
        self.assertEqual(self.message.consumer_tag, self.consumer_tag)
        self.assertEqual(self.message.delivery_tag, self.delivery_tag)
        self.assertEqual(self.message.redelivered, self.redelivered)
        self.assertIsNone(self.message.message_count)
        self.assertIsNone(self.message.reply_code)
        self.assertIsNone(self.message.reply_text)
        self.compare_message()


class BasicGetOkTestCase(TestCase):

    def setUp(self) -> None:
        self.delivery_tag = random.randint(0, 100000000)
        self.message_count = random.randint(0, 1000)
        self.redelivered = bool(random.randint(0, 1))
        super().setUp()

    def get_method(self):
        return commands.Basic.GetOk(
            self.delivery_tag, self.redelivered, self.exchange,
            self.routing_key, self.message_count)

    def test_properties(self):
        self.assertEqual(self.message.delivery_tag, self.delivery_tag)
        self.assertEqual(self.message.message_count, self.message_count)
        self.assertEqual(self.message.redelivered, self.redelivered)
        self.assertIsNone(self.message.reply_code)
        self.assertIsNone(self.message.reply_text)
        self.compare_message()


class BasicReturnTestCase(TestCase):

    def setUp(self) -> None:
        self.reply_code = random.randint(200, 500)
        self.reply_text = str(uuid.uuid4())
        super().setUp()

    def get_method(self):
        return commands.Basic.Return(
            self.reply_code, self.reply_text, self.exchange, self.routing_key)

    def test_properties(self):
        self.assertEqual(self.message.reply_code, self.reply_code)
        self.assertEqual(self.message.reply_text, self.reply_text)
        self.assertIsNone(self.message.consumer_tag)
        self.assertIsNone(self.message.delivery_tag)
        self.assertIsNone(self.message.message_count)
        self.assertIsNone(self.message.redelivered)
        self.compare_message()
