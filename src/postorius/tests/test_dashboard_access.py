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
class TestDashboardAccess(TestCase):
    """Tests for the Dashboard Access for Different Roles.
    """

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
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

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def tearDown(self):
        self.user.delete()
        self.owner.delete()
        self.moderator.delete()
        self.su.delete()

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_user_not_has_control_access(self):
        self.client.login(username='testuser', password='pwd')
        access_result = has_control_access(self.user, [self.test_list])
        self.assertFalse(access_result)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_owner_has_control_access(self):
        self.client.login(username='testowner', password='pwd')
        access_result = has_control_access(self.owner, [self.test_list])
        self.assertTrue(access_result)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_moderator_has_control_access(self):
        self.client.login(username='testmoderator', password='pwd')
        access_result = has_control_access(self.moderator, [self.test_list])
        self.assertTrue(access_result)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_superuser_has_control_access(self):
        self.client.login(username='testsu', password='supwd')
        access_result = has_control_access(self.su, [self.test_list])
        self.assertTrue(access_result)
        self.client.logout()


    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_allowed_lists_for_roles(self):
        # Tests Restricted Access For Accessable Lists on Dashboard
        res_lists = allowed_lists(self.owner, [self.test_list])
        self.assertEqual(len(res_lists), 1)
        res_lists = allowed_lists(self.user, [self.test_list])
        self.assertEqual(len(res_lists), 0)
        res_lists = allowed_lists(self.moderator, [self.test_list])
        self.assertEqual(len(res_lists), 1)
        res_lists = allowed_lists(self.su, [self.test_list])
        self.assertEqual(len(res_lists), 1)

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_event_steamer_view_restricted(self):
        # Tests Restricted View of Event Streamer Widget
        self.client.login(username='testuser', password='pwd')
        self.client.post(reverse('list_subscribe', args=('testlist.example.com', )),
                                    {'email': 'lorem@example.org'})
        self.client.logout()
        self.client.login(username='testmoderator', password='pwd')
        task = create_subscription_tasks([self.test_list])[0]
        self.client.post(reverse('handle_sub_task', args=('testlist.example.com', task.task_id, 'reject' )))
        self.assertEqual(len(EventTracker.objects.filter(event='subscription-reject')), 1)
        res_events = events_allowed(self.user, EventTracker.objects.all())
        self.assertEqual(len(res_events), 0)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_tasks_view_restricted(self):
        # Tests owners and moderators dont get access outside their privelege level
        self.client.login(username='testuser', password='pwd')
        self.client.post(reverse('list_subscribe', args=('testlist.example.com', )),
                                    {'email': 'lorem@example.org'})
        self.client.logout()
        sub_task = create_subscription_tasks([self.test_list])[0]
        mod_task = create_moderation_tasks([self.test_list])[0]
        self.client.login(username='testowner', password='pwd')
        res_tasks = filter_tasks_by_role(self.owner, [sub_task], [self.test_list])
        self.assertEqual(len(res_tasks), 1)
        self.client.logout()
        self.client.login(username='testmoderator', password='pwd')
        res_tasks = filter_tasks_by_role(self.moderator, [mod_task], [self.test_list])
        self.assertEqual(len(res_tasks), 1)
        self.client.logout()
        self.test_list.discard_request(sub_task.task_id)
        sub_task.delete()
        mod_task.delete()
