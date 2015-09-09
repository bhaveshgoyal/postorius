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
"""Tests for Archival Options"""


from __future__ import (
    absolute_import, division, print_function, unicode_literals)

__metaclass__ = type


import mock
import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, RequestFactory, TestCase
from django.test.utils import override_settings
try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.error import HTTPError

from postorius.forms import ListArchiverForm
from postorius.tests import MM_VCR
from postorius.tests.mailman_api_tests import API_CREDENTIALS
from postorius.utils import get_client
from postorius.views.list import _add_archival_messages


logger = logging.getLogger(__name__)
vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.WARNING)


@override_settings(**API_CREDENTIALS)
class ArchivalOptionsAccessTest(TestCase):

    @MM_VCR.use_cassette('archival_options.yaml')
    def setUp(self):
        # Create domain `example.com` in Mailman
        try:
            example_com = get_client().create_domain('example.com')
        except HTTPError:
            example_com = get_client().get_domain('example.com')
        self.m_list = example_com.create_list('test_list')
        self.test_user = User.objects.create_user(
            'test_user', 'test_user@example.com', 'pwd')
        self.test_superuser = User.objects.create_superuser(
            'test_superuser', 'test_superuser@example.com', 'pwd')

    @MM_VCR.use_cassette('archival_options.yaml')
    def tearDown(self):
        self.test_user.delete()
        self.test_superuser.delete()
        self.m_list.delete()

    @MM_VCR.use_cassette('archival_options.yaml')
    def test_no_access_for_unauthenticated_user(self):
        response = self.client.get(reverse('list_archival_options',
                                   args=('test_list.example.com', )))
        self.assertEqual(response.status_code, 403)

    @MM_VCR.use_cassette('archival_options.yaml')
    def test_no_access_for_unauthenticated_user(self):
        self.client.login(username=self.test_superuser.username,
                          password='pwd')
        response = self.client.get(reverse('list_archival_options',
                                   args=('test_list.example.com', )))
        self.assertEqual(response.status_code, 200)


@override_settings(**API_CREDENTIALS)
class ArchivalOptions(TestCase):

    @MM_VCR.use_cassette('test_list_archival_options.yaml')
    def setUp(self):
        # Create domain `example.com` in Mailman.
        try:
            example_com = get_client().create_domain('example.com')
        except HTTPError:
            example_com = get_client().get_domain('example.com')
        self.m_list = example_com.create_list('test_list')
        self.test_user = User.objects.create_user(
            'test_user', 'test_user@example.com', 'pwd')
        self.test_superuser = User.objects.create_superuser(
            'test_superuser', 'test_superuser@example.com', 'pwd')
        self.client.login(username=self.test_superuser.username,
                          password='pwd')

    @MM_VCR.use_cassette('test_list_archival_options.yaml')
    def tearDown(self):
        self.test_user.delete()
        self.test_superuser.delete()
        self.m_list.delete()

    @MM_VCR.use_cassette('test_list_archival_options.yaml')
    def test_context_contains_list_archivers(self):
        response = self.client.get(reverse('list_archival_options',
                                   args=('test_list.example.com', )))
        self.assertTrue('archivers' in response.context)

    @MM_VCR.use_cassette('test_list_archival_options.yaml')
    def test_context_contains_the_right_form(self):
        response = self.client.get(reverse('list_archival_options',
                                   args=('test_list.example.com', )))
        self.assertEqual(type(response.context['form']), ListArchiverForm)

    def test_post_data_is_correctly_processed(self):
        with MM_VCR.use_cassette('test_list_archival_options.yaml'):
            archivers = self.m_list.archivers
            # Archiver is enabled by default.
            self.assertTrue(archivers['mail-archive'])

        with MM_VCR.use_cassette('test_list_archival_options_disable_archiver.yaml'):
            # Archiver is disabled after it's deactivated in the form.
            response = self.client.post(
                reverse('list_archival_options', args=('test_list.example.com', )),
                {'archivers': ['mhonarc', 'prototype']})
            self.assertFalse(self.m_list.archivers['mail-archive'])

        with MM_VCR.use_cassette('test_list_archival_options_enable_archiver.yaml'):
            # Archiver is disabled after it's deactivated in the form.
            response = self.client.post(
                reverse('list_archival_options', args=('test_list.example.com', )),
                {'archivers': ['mail-archive']})
            self.assertTrue(self.m_list.archivers['mail-archive'])


class ArchivalMessagesTest(TestCase):
    """
    Tests the ``_add_archival_messages`` helper method.
    """

    def setUp(self):
        factory = RequestFactory()
        self.request = factory.get('/')

    @mock.patch('django.contrib.messages.success')
    @mock.patch('django.contrib.messages.warning')
    def test_warning_messages(self, mock_warning, mock_success):
        # foo-archiver enabled, but not stored adds warning message.
        _add_archival_messages(['foo-archiver'], [], {'foo-archiver': False}, self.request)
        self.assertTrue('could not be enabled' in mock_warning.call_args[0][1])
        self.assertTrue('foo-archiver' in mock_warning.call_args[0][1])
        # messages.success should not have been called.
        self.assertEqual(mock_success.call_count, 0)

    @mock.patch('django.contrib.messages.success')
    @mock.patch('django.contrib.messages.warning')
    def test_success_messages(self, mock_warning, mock_success):
        # foo-archiver enabled and stored adds success message.
        _add_archival_messages(['foo-archiver'], [], {'foo-archiver': True}, self.request)
        self.assertTrue('activated new archivers' in mock_success.call_args[0][1])
        self.assertTrue('foo-archiver' in mock_success.call_args[0][1])
        # messages.warning should not have been called.
        self.assertEqual(mock_warning.call_count, 0)
