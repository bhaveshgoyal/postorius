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
class ListIndexPageTest(SimpleTestCase):
    """Tests for the list index page."""

    @MM_VCR.use_cassette('test_list_index.yaml')
    def setUp(self):
        self.client = Client()
        try:
            self.domain = get_client().create_domain('example.com')
        except HTTPError:
            self.domain = get_client().get_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.bar_list = self.domain.create_list('bar')

    @MM_VCR.use_cassette('test_list_index.yaml')
    def tearDown(self):
        for mlist in get_client().lists:
            mlist.delete()

    @MM_VCR.use_cassette('test_list_index.yaml')
    def test_list_index_contains_the_lists(self):
        # The list index page should contain the lists
        response = self.client.get(reverse('list_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['lists']), 2)
        # The lists should be sorted by address
        self.assertEqual([l.fqdn_listname for l in response.context['lists']],
                         ['bar@example.com', 'foo@example.com'])
