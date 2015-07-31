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

from email import message_from_string
from django import template

register = template.Library()


@register.filter(name='strip_email')
def strip_email(email_text):
    """Strip most of the headers from the email for the
    held messages view.

    Only these headers would be kept:
    - To
    - From
    - Date
    - CC
    - Subject

    If available, show only the text part of the email.

    TODO: maxking - modify this later to extract text from HTML
    to be displayed there.
    """
    msg = message_from_string(email_text)

    content_type = msg.get_content_type()
    if content_type == 'multipart/alternative':
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                msg.set_payload(part.as_string())

    show_headers = ['To', 'From', 'Date', 'CC', 'Subject']
    for header in msg.keys():
        if header not in show_headers:
            del msg[header]

    return msg.as_string()
