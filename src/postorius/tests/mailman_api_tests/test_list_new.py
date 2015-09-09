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
import time
import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, SimpleTestCase
from django.test.utils import override_settings
try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.error import HTTPError

from postorius.utils import get_client
from postorius.tests import MM_VCR


logger = logging.getLogger(__name__)
vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.WARNING)


API_CREDENTIALS = {'MAILMAN_API_URL': 'http://localhost:9001',
                   'MAILMAN_USER': 'restadmin',
                   'MAILMAN_PASS': 'restpass'}


@override_settings(**API_CREDENTIALS)
class ListCreationTest(SimpleTestCase):
    """Tests for the new list page."""

    @MM_VCR.use_cassette('test_list_creation.yaml')
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('user', 'user@example.com', 'pwd')
        self.superuser = User.objects.create_superuser('su', 'su@example.com',
                                                       'pwd')
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')

    @MM_VCR.use_cassette('test_list_creation.yaml')
    def tearDown(self):
        self.user.delete()
        self.superuser.delete()
        for mlist in get_client().lists:
            mlist.delete()

    def test_permission_denied(self):
        self.client.login(username='user', password='pwd')
        response = self.client.get(reverse('list_new'))
        self.assertEqual(
            response['location'],
            'http://testserver/postorius/accounts/login/?next=/lists/new/')

    @MM_VCR.use_cassette('test_list_creation.yaml')
    def test_new_list_created_with_owner(self):
        self.client.login(username='su', password='pwd')
        post_data = {'listname': 'a_new_list',
                     'mail_host': 'example.com',
                     'list_owner': 'owner@example.com',
                     'advertised': 'True',
                     'description': 'A new list.'}
        self.client.post(reverse('list_new'), post_data)
        a_new_list = get_client().get_list('a_new_list@example.com')
        self.assertEqual(a_new_list.fqdn_listname, u'a_new_list@example.com')
        self.assertEqual(a_new_list.owners, [u'owner@example.com'])
