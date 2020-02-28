# Copyright (c) 2017 LINE Corporation
# These sources are released under the terms of the MIT license: see LICENSE

from unittest import mock

from django.test import override_settings
from django.urls import reverse

from promgen import models, tests
from promgen.notification.email import NotificationEmail

TEST_SETTINGS = tests.Data('examples', 'promgen.yml').yaml()
TEST_ALERT = tests.Data('examples', 'alertmanager.json').json()


class EmailTest(tests.PromgenTest):
    @mock.patch('django.dispatch.dispatcher.Signal.send')
    def setUp(self, mock_signal):
        self.shard = models.Shard.objects.create(name='test.shard')
        self.service = models.Service.objects.create(name='test.service')
        self.project = models.Project.objects.create(name='test.project', service=self.service, shard=self.shard)
        self.project2 = models.Project.objects.create(name='other.project', service=self.service, shard=self.shard)
        self.sender = models.Sender.objects.create(
            obj=self.project,
            sender=NotificationEmail.__module__,
            value='example@example.com',
        )
        models.Sender.objects.create(
            obj=self.project,
            sender=NotificationEmail.__module__,
            value='foo@example.com',
        )
        models.Sender.objects.create(
            obj=self.project2,
            sender=NotificationEmail.__module__,
            value='bar@example.com',
        )

    @override_settings(PROMGEN=TEST_SETTINGS)
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('promgen.notification.email.send_mail')
    def test_email(self, mock_email):
        self.client.post(reverse('alert'),
            data=TEST_ALERT,
            content_type='application/json'
        )

        _SUBJECT = tests.Data('notification', 'email.subject.txt').raw().strip()
        _MESSAGE = tests.Data('notification', 'email.body.txt').raw().strip()

        mock_email.assert_has_calls([
            mock.call(
                _SUBJECT,
                _MESSAGE.format(service=self.service, project=self.project),
                'promgen@example.com',
                ['example@example.com']
            ),
            mock.call(
                _SUBJECT,
                _MESSAGE.format(service=self.service, project=self.project),
                'promgen@example.com',
                ['foo@example.com']
            )
        ], any_order=True)
        # Three senders are registered but only two should trigger
        self.assertTrue(mock_email.call_count == 2)