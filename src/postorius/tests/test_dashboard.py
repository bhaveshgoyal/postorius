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
    has_control_access, create_subscription_tasks, sync_tasks_to_current, allowed_lists)
from postorius.models import AdminTasks

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
            self.test_list = self.domain.create_list('test_list')
        except HTTPError:
            self.test_list = get_client().get_list('test_list.example.com')
        self.user = User.objects.create_user(
            'testuser', 'testuser@example.com', 'pwd')
        self.owner = User.objects.create_user(
            'testowner', 'testowner@example.com', 'pwd')
        self.moderator = User.objects.create_user(
            'testmoderator', 'testmoderator@example.com', 'pwd')
        self.su = User.objects.create_superuser(
            'testsu', 'testsu@example.com', 'supwd')
        self.test_list.add_owner('testowner@example.com')
        self.test_list.add_moderator('testmoderator@example.com')

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def tearDown(self):
        self.test_list.delete()
        self.user.delete()
        self.owner.delete()
        self.moderator.delete()
        self.su.delete()

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_user_not_has_control_access(self):
        self.client.login(username='testuser', password='pwd')
        access_result = has_control_access(self.user, [self.test_list])
        self.assertEqual(access_result, False)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_owner_has_control_access(self):
        self.client.login(username='testowner', password='pwd')
        access_result = has_control_access(self.owner, [self.test_list])
        self.assertEqual(access_result, True)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_moderator_has_control_access(self):
        self.client.login(username='testmoderator', password='pwd')
        access_result = has_control_access(self.moderator, [self.test_list])
        self.assertEqual(access_result, True)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_superuser_has_control_access(self):
        self.client.login(username='testsu', password='supwd')
        access_result = has_control_access(self.su, [self.test_list])
        self.assertEqual(access_result, True)
        self.client.logout()


    @MM_VCR.use_cassette('test_dashboard_access.yaml')
    def test_allowed_lists_for_roles(self):
        res_lists = allowed_lists(self.owner, [self.test_list])
        self.assertEqual(len(res_lists), 1)
        res_lists = allowed_lists(self.user, [self.test_list])
        self.assertEqual(len(res_lists), 0)
        res_lists = allowed_lists(self.moderator, [self.test_list])
        self.assertEqual(len(res_lists), 1)
        res_lists = allowed_lists(self.su, [self.test_list])
        self.assertEqual(len(res_lists), 1)


@override_settings(**API_CREDENTIALS)
class TestTaskManagenent(TestCase):
    """Tests for Operations Performed on Tasks.

    Tests Tasks creation, auto deletion and other
    operations such as filteration, reordering etc.
    """

    @MM_VCR.use_cassette('test_task_management.yaml')
    def setUp(self):
        self.client = Client()
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')
        try:
            self.test_list = self.domain.create_list('test_list')
        except HTTPError:
            self.test_list = get_client().get_list('test_list.example.com')
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
        self.test_list.add_owner('testowner@example.com')
        self.test_list.add_moderator('testmoderator@example.com')

    @MM_VCR.use_cassette('test_task_management.yaml')
    def tearDown(self):
        self.test_list.delete()
        self.user.delete()
        self.owner.delete()
        self.moderator.delete()
        self.su.delete()
	AdminTasks.objects.all().delete()

    @MM_VCR.use_cassette('test_task_management.yaml')
    def test_subscription_task_created(self):
        # Make a Subscription Request
        self.client.login(username='testuser', password='pwd')
        self.client.post(reverse('list_subscribe', args=('test_list.example.com', )),
                                    {'email': 'lorem@example.org'})
        self.client.logout()
        # Adds The Request To Pending Tasks List
	create_subscription_tasks([self.test_list])
        self.assertEqual(AdminTasks.objects.filter(task_type='subscription').count(), 1)
        # Check Recreations don't occur
        create_subscription_tasks([self.test_list])
        self.assertEqual(AdminTasks.objects.filter(task_type='subscription').count(), 1)


#   @MM_VCR.use_cassette('test_task_creation.yaml')
#TODO def test_moderation_task_created(self):
#        pass

    @MM_VCR.use_cassette('test_task_management.yaml')
    def test_manual_task_created(self):
        self.client.login(username='testowner', password='pwd')
        mtask_data = {'mtask_subject': 'This is a Reminder',
                      'mtask_description': 'It actually is a reminder'}
        self.client.post(reverse('user_dashboard'), mtask_data)
        mtask = AdminTasks.objects.filter(task_type='manual').filter(user_email='testowner@example.com')
        self.assertNotEqual(len(mtask),0)
        self.client.logout()

    @MM_VCR.use_cassette('test_task_management.yaml')
    def test_task_auto_syncing(self):
        # Make a Subscription Request
        self.client.login(username='testuser', password='pwd')
        self.client.post(reverse('list_subscribe', args=('test_list.example.com', )),
                                    {'email': 'lorem@example.org'})
        self.client.logout()
	create_subscription_tasks([self.test_list])
        for each in self.test_list.requests:
            self.test_list.discard_request(each['token'])
        sync_tasks_to_current([self.test_list])
        self.assertEqual(len(AdminTasks.objects.filter(task_type='subscription')),0)


