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
from urllib2 import HTTPError

from postorius.tests import MM_VCR
from postorius.utils import get_client
from postorius.views.user import (
    has_control_access, create_subscription_tasks, create_moderation_tasks, sync_tasks_to_current, allowed_lists, events_allowed, filter_tasks_by_role)
from postorius.views.list import handle_sub_task
from postorius.models import AdminTasks, EventTracker, List

logger = logging.getLogger(__name__)
vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.WARNING)


API_CREDENTIALS = {'MAILMAN_API_URL': 'http://localhost:9001',
                   'MAILMAN_USER': 'restadmin',
                   'MAILMAN_PASS': 'restpass'}

@override_settings(**API_CREDENTIALS)
class TestModerationTaskManagement(TestCase):
    """Tests for Operations Performed on Moderation Requests.

    Tests Tasks creation, auto deletion along 
    with Event Creation and other operations 
    such as filteration, prioritizing etc.
    """


    @MM_VCR.use_cassette('test_dashboardmod_management.yaml')
    def setUp(self):
        self.client = Client()
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')
        try:
            self.test_list = self.domain.create_list('testlist')
        except HTTPError:
            self.test_list = get_client().get_list('testlist.example.com')
        settings = self.test_list.settings
        settings['subscription_policy'] = 'moderate'
        settings.save()
        self.user = User.objects.create_user(
            'testuser', 'testuser@example.com', 'pwd')
        self.owner = User.objects.create_user(
            'testowner', 'testowner@example.com', 'pwd')
        self.moderator = User.objects.create_user(
            'testmoderator', 'testmoderator@example.com', 'pwd')
        self.su = User.objects.create_superuser(
            'testsu', 'testsu@example.com', 'supwd')
        if self.owner.email not in self.test_list.owners:
            self.test_list.add_owner('testowner@example.com')
        if self.moderator.email not in self.test_list.moderators:
            self.test_list.add_moderator('testmoderator@example.com')
        self.tasks = create_moderation_tasks([self.test_list])[0]
        self.task = sync_tasks_to_current([self.test_list])[0]

    @MM_VCR.use_cassette('test_dashboardmod_management.yaml')
    def tearDown(self):
        self.user.delete()
        self.owner.delete()
        self.moderator.delete()
        self.su.delete()

    @MM_VCR.use_cassette('test_dashboardmod_management.yaml')
    def test_mod_tasks_created(self):
        # Tests Moderation and Subscription Tasks Creation
        # Adds The Request To Pending Tasks List
        self.assertIsNotNone(self.task)
        # Check Recreations don't occur
        recreation = create_moderation_tasks([self.test_list])
        self.assertEqual(len(recreation),0)


    @MM_VCR.use_cassette('test_dashboardmod_management.yaml')
    def test_mod_accepted_event_created(self):
        self.client.login(username='testmoderator', password='pwd')
        self.client.post(reverse('handle_mod_task', args=('testlist.example.com', self.task.task_id, 'accept' )))
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('accepted a post' in response.content)
        self.client.logout() 


    @MM_VCR.use_cassette('test_dashboardmod_management.yaml')
    def test_mod_discarded_event_created(self):
        self.client.login(username='testmoderator', password='pwd')
        self.client.post(reverse('handle_mod_task', args=('testlist.example.com', self.task.task_id, 'discard' )))
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('discarded a post' in response.content)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboardmod_management.yaml')
    def test_mod_deferred_event_created(self):
        self.client.login(username='testmoderator', password='pwd')
        self.client.post(reverse('handle_mod_task', args=('testlist.example.com', self.task.task_id, 'defer' )))
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('defered a post' in response.content)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboardmod_management.yaml')
    def test_mod_reject_event_created(self):
        self.client.login(username='testmoderator', password='pwd')
        self.client.post(reverse('handle_mod_task', args=('testlist.example.com', self.task.task_id, 'reject' )))
        response = self.client.get(reverse('user_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('rejected a post' in response.content)
        self.client.logout() 
