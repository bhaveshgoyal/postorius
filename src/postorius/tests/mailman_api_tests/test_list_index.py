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

from django.core.urlresolvers import reverse
from django.test import Client, SimpleTestCase
from django.test.utils import override_settings
from urllib2 import HTTPError

from postorius.utils import get_client
from postorius.tests import MM_VCR


logger = logging.getLogger(__name__)
vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.WARNING)


API_CREDENTIALS = {'MAILMAN_API_URL': 'http://localhost:9001',
                   'MAILMAN_USER': 'restadmin',
                   'MAILMAN_PASS': 'restpass'}


@override_settings(**API_CREDENTIALS)
class ListIndexPageTest(SimpleTestCase):
    """Tests for the list index page."""

    @MM_VCR.use_cassette('test_list_index.yaml')
    def setUp(self):
        self.client = Client()
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')

        try:
            self.net_domain = get_client().create_domain('example.net')
        except HTTPError:
            self.net_domain = get_client().get_domain('example.net')

        self.foo_list = self.domain.create_list('foo')

    @MM_VCR.use_cassette('test_list_index.yaml')
    def tearDown(self):
        for mlist in get_client().lists:
            mlist.delete()

    @MM_VCR.use_cassette('test_list_index.yaml')
    def test_list_index_contains_one_list(self):
        # The list index page should contain the
        response = self.client.get(reverse('list_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['lists']), 1)
        self.assertEqual(response.context['lists'][0].fqdn_listname,
                         'foo@example.com')

    @override_settings(FILTER_VHOST=True)
    @MM_VCR.use_cassette('test_list_index.yaml')
    def test_filter_lists_by_domain(self):
        """List Index page should show lists only from the
        domain the Postorius is being served from.
        """
        response = self.client.get(reverse('list_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['lists']), 0)
        boo_list = self.net_domain.create_list('boo')
        response = self.client.get(reverse('list_index'), HTTP_HOST='www.example.net')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['lists']), 1)
        self.assertEqual(response.context['lists'][0].fqdn_listname,
                         'boo@example.net')
