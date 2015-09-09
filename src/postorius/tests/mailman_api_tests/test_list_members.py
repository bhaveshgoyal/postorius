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
class ListMembersAccessTest(TestCase):
    """Tests for the list members page.

    Tests permissions and creation of list owners and moderators.
    """

    @MM_VCR.use_cassette('list_members_access.yaml')
    def setUp(self):
        self.client = Client()
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')
        try:
            self.foo_list = self.domain.create_list('foo')
        except HTTPError:
            self.foo_list = get_client().get_list('foo.example.com')
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass')
        self.superuser = User.objects.create_superuser(
            'testsu', 'su@example.com', 'testpass')
        self.owner = User.objects.create_user(
            'testowner', 'owner@example.com', 'testpass')
        self.moderator = User.objects.create_user(
            'testmoderator', 'moderator@example.com', 'testpass')
        self.foo_list.add_owner('owner@example.com')
        self.foo_list.add_moderator('moderator@example.com')

    @MM_VCR.use_cassette('list_members_access.yaml')
    def tearDown(self):
        self.foo_list.delete()
        self.user.delete()
        self.superuser.delete()
        self.owner.delete()
        self.moderator.delete()

    @MM_VCR.use_cassette('list_members_access.yaml')
    def test_page_not_accessible_if_not_logged_in(self):
        response = self.client.get(reverse('list_members',
                                           args=('foo@example.com', )))
        self.assertEqual(response.status_code, 403)

    @MM_VCR.use_cassette('list_members_access.yaml')
    def test_page_not_accessible_for_unprivileged_users(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('list_members',
                                           args=('foo@example.com', )))
        self.assertEqual(response.status_code, 403)

    @MM_VCR.use_cassette('list_members_page.yaml')
    def test_not_accessible_for_moderator(self):
        self.client.login(username='testmoderator', password='testpass')
        response = self.client.get(reverse('list_members',
                                           args=('foo@example.com', )))
        self.assertEqual(response.status_code, 403)

    @MM_VCR.use_cassette('list_members_page.yaml')
    def test_page_accessible_for_superuser(self):
        self.client.login(username='testsu', password='testpass')
        response = self.client.get(reverse('list_members',
                                           args=('foo@example.com', )))
        self.assertEqual(response.status_code, 200)

    @MM_VCR.use_cassette('list_members_page.yaml')
    def test_page_accessible_for_owner(self):
        self.client.login(username='testowner', password='testpass')
        response = self.client.get(reverse('list_members',
                                           args=('foo@example.com', )))
        self.assertEqual(response.status_code, 200)


@override_settings(**API_CREDENTIALS)
class AddOwnerTest(TestCase):
    """Tests for the list members page.

    Tests creation of list owners.
    """

    @MM_VCR.use_cassette('test_list_members_add_owner.yaml')
    def setUp(self):
        self.client = Client()
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.su = User.objects.create_superuser(
            'su', 'su@example.com', 'pwd')
        # login and post new owner data to url
        self.client.login(username='su', password='pwd')
        self.client.post(
            reverse('list_members', args=('foo@example.com', )),
            {'owner_email': 'newowner@example.com'})
        owners = self.foo_list.owners

    @MM_VCR.use_cassette('test_list_members_add_owner.yaml')
    def tearDown(self):
        self.foo_list.delete()
        self.su.delete()

    @MM_VCR.use_cassette('test_list_members_add_owner_new_owner_added.yaml')
    def test_new_owner_added(self):
        self.assertTrue(u'newowner@example.com' in self.foo_list.owners)


@override_settings(**API_CREDENTIALS)
class AddModeratorTest(TestCase):
    """Tests for the list members page.

    Tests creation of moderators.
    """

    @MM_VCR.use_cassette('test_list_members_add_moderator.yaml')
    def setUp(self):
        self.client = Client()
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.su = User.objects.create_superuser(
            'su', 'su@example.com', 'pwd')
        # login and post new moderator data to url
        self.client.login(username='su', password='pwd')
        self.client.post(
            reverse('list_members', args=('foo@example.com', )),
            {'moderator_email': 'newmod@example.com'})
        moderators = self.foo_list.moderators

    @MM_VCR.use_cassette('test_list_members_add_moderator.yaml')
    def tearDown(self):
        self.foo_list.delete()
        self.su.delete()

    @MM_VCR.use_cassette('test_list_members_new_moderator_added.yaml')
    def test_new_moderator_added(self):
        self.assertTrue(u'newmod@example.com' in self.foo_list.moderators)
