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
from django.db import IntegrityError
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
class ModelTest(SimpleTestCase):
    """Tests for the list index page."""

    @MM_VCR.use_cassette('test_model.yaml')
    def setUp(self):
        self.client = Client()
        self.mmclient = get_client()
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')
        self.foo_list = self.domain.create_list('foo')

    @MM_VCR.use_cassette('test_model.yaml')
    def tearDown(self):
        for mlist in self.mmclient.lists:
            mlist.delete()
        for user in self.mmclient.users:
            user.delete()
        User.objects.all().delete()

    @MM_VCR.use_cassette('test_model-2.yaml')
    def test_mailman_user_not_created_when_flag_is_off(self):
        with self.settings(AUTOCREATE_MAILMAN_USER=False):
            User.objects.create_user('testuser', 'test@example.com', 'testpass')
            with self.assertRaises(HTTPError):
                self.mmclient.get_user('test@example.com')

    @MM_VCR.use_cassette('test_model.yaml')
    def test_mailman_user_created_when_flag_is_on(self):
        with self.settings(AUTOCREATE_MAILMAN_USER=True):
            User.objects.create_user('testuser', 'test@example.com', 'testpass')
            user = self.mmclient.get_user('test@example.com')
            self.assertEqual(str(user.addresses[0]), 'test@example.com')
