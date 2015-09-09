# -*- coding: utf-8 -*-
# Copyright (C) 1998-2015 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Postorius.  If not, see <http://www.gnu.org/licenses/>.
import logging

from django.conf import settings
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from mailmanclient import Client


logger = logging.getLogger(__name__)


def get_client():
    return Client('{0}/3.0'.format(settings.MAILMAN_API_URL),
                  settings.MAILMAN_USER,
                  settings.MAILMAN_PASS)


def render_api_error(request):
    """Renders an error template.
    Use if MailmanApiError is catched.
    """
    return render_to_response(
        'postorius/errors/generic.html',
        {'error': "Mailman REST API not available.  "
                  "Please start Mailman core."},
        context_instance=RequestContext(request))
