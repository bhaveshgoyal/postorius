# -*- coding: utf-8 -*-
# Copyright (C) 2012-2015 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Postorius.  If not, see <http://www.gnu.org/licenses/>.
import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.test.utils import override_settings
try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.error import HTTPError

from postorius.tests import MM_VCR
from postorius.utils import get_client


logger = logging.getLogger(__name__)
vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.WARNING)


API_CREDENTIALS = {'MAILMAN_API_URL': 'http://localhost:9001',
                   'MAILMAN_USER': 'restadmin',
                   'MAILMAN_PASS': 'restpass'}


@override_settings(**API_CREDENTIALS)
class TestSubscriptionPolicyOpen(TestCase):
    """Tests for the list members page.

    Tests permissions and creation of list owners and moderators.
    """

    @MM_VCR.use_cassette('test_list_subscription.yaml')
    def setUp(self):
        self.client = Client()
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')
        try:
            self.test_list = self.domain.create_list('open_list')
        except HTTPError:
            self.test_list = get_client().get_list('open_list.example.com')
        # Set subscription policy to open
        settings = self.test_list.settings
        settings['subscription_policy'] = 'open'
        settings.save()
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'pwd')

    @MM_VCR.use_cassette('test_list_subscription.yaml')
    def tearDown(self):
        self.test_list.delete()
        self.user.delete()

    @MM_VCR.use_cassette('test_list_subscription.yaml')
    def test_subscribing_adds_member(self):
        # The subscription goes straight through.
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('open_list.example.com', )),
            {'email': 'fritz@example.org'})
        self.assertEqual(len(self.test_list.members), 1)
        self.assertEqual(len(self.test_list.requests), 0)


@override_settings(**API_CREDENTIALS)
class TestSubscriptionPolicyModerate(TestCase):
    """Tests for the list members page.

    Tests permissions and creation of list owners and moderators.
    """

    @MM_VCR.use_cassette('test_list_subscription_moderate.yaml')
    def setUp(self):
        self.client = Client()
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')
        try:
            self.test_list = self.domain.create_list('moderate_subs')
        except HTTPError:
            self.test_list = get_client().get_list('moderate_subs.example.com')
        # Set subscription policy to open
        settings = self.test_list.settings
        settings['subscription_policy'] = 'moderate'
        settings.save()
        # Create django user.
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'pwd')

    @MM_VCR.use_cassette('test_list_subscription_moderate.yaml')
    def tearDown(self):
        self.test_list.delete()
        self.user.delete()

    @MM_VCR.use_cassette('test_list_subscription_moderate.yaml')
    def test_subscribing_adds_member(self):
        # The subscription is held for approval.
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('moderate_subs.example.com', )),
            {'email': 'fritz@example.org'})
        self.assertEqual(len(self.test_list.members), 0)
        self.assertEqual(len(self.test_list.requests), 1)
