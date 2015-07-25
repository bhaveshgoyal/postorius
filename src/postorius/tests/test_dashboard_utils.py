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
from datetime import datetime, timedelta, date
from postorius.tests import MM_VCR
from postorius.utils import get_client
from postorius.views.user import generate_graph_object, create_subscription_tasks
logger = logging.getLogger(__name__)
vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.WARNING)


API_CREDENTIALS = {'MAILMAN_API_URL': 'http://localhost:9001',
                   'MAILMAN_USER': 'restadmin',
                   'MAILMAN_PASS': 'restpass'}


@override_settings(**API_CREDENTIALS)
class TestDashboardRoleRemoval(TestCase):
    """Tests for Dashboard Role Removal methods.
    """

    @MM_VCR.use_cassette('test_dashboard_utils.yaml')
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
        settings['subscription_policy'] = 'open'
        settings.save()
        self.owner = User.objects.create_user(
            'testowner', 'testowner@example.com', 'pwd')
        self.moderator = User.objects.create_user(
            'testmoderator', 'testmoderator@example.com', 'pwd')
        self.su = User.objects.create_superuser(
            'testsu', 'testsu@example.com', 'supwd')

    @MM_VCR.use_cassette('test_dashboard_utils.yaml')
    def tearDown(self):
        self.owner.delete()
        self.moderator.delete()
        self.su.delete()
        self.test_list.delete()

    @MM_VCR.use_cassette('test_dashboard_utils.yaml')
    def test_remove_owner_role(self):
        self.client.login(username='testsu', password='supwd')
        self.test_list.add_owner('testowner@example.com')
        response = self.client.post(reverse('remove_role_tasks', args=(self.test_list.list_id, 'owner', self.owner.email)))
        self.assertFalse(u'testowner@example.com' in self.test_list.owners)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboard_utils.yaml')
    def test_remove_moderator_role(self):
        self.client.login(username='testsu', password='supwd')
        self.test_list.add_moderator('testmoderator@example.com')
        response = self.client.post(reverse('remove_role_tasks', args=(self.test_list.list_id, 'moderator', self.moderator.email)))
        self.assertFalse(u'testmoderator@example.com' in self.test_list.moderators)
        self.client.logout()

    @MM_VCR.use_cassette('test_dashboard_utils.yaml')
    def test_unsubscribe_member(self):
        self.client.login(username='testsu', password='supwd') 
        self.client.post(reverse('list_subscribe', args=('testlist.example.com', )),
                                 {'email': 'testmember@example.com'})
        self.assertEqual(len(self.test_list.members),1)
        response = self.client.post(reverse('remove_role_tasks', args=(self.test_list.list_id, 'subscriber', 'testmember@example.com')))
        self.assertEqual(len(self.test_list.members),0)
        self.client.logout()


@override_settings(**API_CREDENTIALS)
class TestDashboardGraphGenerator(TestCase):
    """Tests for Graph Generation Method.
    """

    @MM_VCR.use_cassette('test_dashboard_utils.yaml')
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
        self.su = User.objects.create_superuser(
            'testsu', 'testsu@example.com', 'supwd')

    @MM_VCR.use_cassette('test_dashboard_utils.yaml')
    def tearDown(self):
        self.test_list.delete()
        self.su.delete()

    @MM_VCR.use_cassette('test_dashboard_utils.yaml')
    def test_dates_generated_till_past_month(self):
        sub_obj, mod_obj = generate_graph_object([self.test_list])
        self.assertEqual(len(sub_obj),31)
        self.assertEqual(len(mod_obj), 31)
        today = datetime.today().date()
        date_start = today + timedelta(days=-30)
        self.assertEqual(sub_obj.keys()[30], today.strftime("%Y-%m-%d"))
        self.assertEqual(mod_obj.keys()[30], today.strftime("%Y-%m-%d"))
        self.assertEqual(sub_obj.keys()[0], date_start.strftime("%Y-%m-%d"))
        self.assertEqual(mod_obj.keys()[0], date_start.strftime("%Y-%m-%d"))

    @MM_VCR.use_cassette('test_dashboard_utils.yaml')
    def test_task_added_to_correct_date(self):
        self.client.login(username='testsu', password='supwd') 
        self.client.post(reverse('list_subscribe', args=('testlist.example.com', )),
                                 {'email': 'testmember@example.com'})
        self.client.logout()
        sub_tasks = create_subscription_tasks([self.test_list])
        sub_obj, mod_obj = generate_graph_object([self.test_list.list_id])
        today = datetime.today().date().strftime("%Y-%m-%d")
        self.assertEqual(sub_obj[today], 1)
        self.assertEqual(mod_obj[today], 0)
