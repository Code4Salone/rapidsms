#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import mock

from django.core.urlresolvers import reverse

from rapidsms.tests.harness import RapidTest


__all__ = ['TestMessagingView', 'TestSendView']


class TestMessagingView(RapidTest):
    url_name = 'messaging'

    def setUp(self):
        self.url = reverse(self.url_name)

    def test_get(self):
        """The messaging page should return a 200 code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class TestSendView(RapidTest):
    url_name = 'send_message'

    def setUp(self):
        self.url = reverse(self.url_name)
        self.backend = self.create_backend({'name': 'mockbackend'})
        self.contact1 = self.create_contact({'name': 'one'})
        self.contact2 = self.create_contact({'name': 'two'})
        self.connection1 = self.create_connection({
            'backend': self.backend,
            'contact': self.contact1,
        })
        self.connection2 = self.create_connection({
            'backend': self.backend,
            'contact': self.contact2,
        })
        self.message = 'hello'
        self.data = {
            'message': self.message,
            'connections_1': [self.connection1.pk, self.connection2.pk],
        }

    def test_get(self):
        """Only POST should be allowed."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_post(self):
        """Posting valid data should cause a 200 response."""
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(self.outbound), 2)
        self.assertEqual(self.outbound[0].connection, self.connection1)
        self.assertEqual(self.outbound[0].text, self.message)
        self.assertEqual(self.outbound[1].connection, self.connection2)
        self.assertEqual(self.outbound[1].text, self.message)

    def test_post_no_message(self):
        """A form validation error should cause a 400 response."""
        self.data.pop('message')
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 400)  # Bad Request

    def test_post_no_contacts(self):
        """A form validation error should cause a 400 response."""
        self.data.pop('connections_1')
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 400)  # Bad Request

    def test_post_send_error(self):
        """
        An error during sending should cause a 500 response. No guarantees
        are made about whether the message has been sent to other recipients.
        """
        with mock.patch('rapidsms.contrib.messaging.forms.MessageForm.send') as send:
            send.side_effect = Exception()
            response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 500)