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


import json


from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,
                                       SetPasswordForm, PasswordChangeForm)
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import Context, loader, RequestContext
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.error import HTTPError
from postorius import utils
from postorius.models import (Domain, List, Member, MailmanUser,
                              MailmanApiError, Mailman404Error)
from postorius.forms import *
from postorius.auth.decorators import *


@login_required
@user_passes_test(lambda u: u.is_superuser)
def site_settings(request):
    return render_to_response('postorius/site_settings.html',
                              context_instance=RequestContext(request))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def domain_index(request):
    try:
        existing_domains = Domain.objects.all()
    except MailmanApiError:
        return utils.render_api_error(request)
    return render_to_response('postorius/domain_index.html',
                              {'domains': existing_domains},
                              context_instance=RequestContext(request))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def domain_new(request):
    message = None
    if request.method == 'POST':
        form = DomainNew(request.POST)
        if form.is_valid():
            domain = Domain(mail_host=form.cleaned_data['mail_host'],
                            base_url=form.cleaned_data['web_host'],
                            description=form.cleaned_data['description'],
                            owner=request.user.email)
            try:
                domain.save()
            except MailmanApiError:
                return utils.render_api_error(request)
            except HTTPError as e:
                messages.error(request, e)
            else:
                messages.success(request, _("New Domain registered"))
            return redirect("domain_index")
    else:
        form = DomainNew()
    return render_to_response('postorius/domain_new.html',
                              {'form': form, 'message': message},
                              context_instance=RequestContext(request))


def domain_delete(request, domain):
    """Deletes a domain but asks for confirmation first.
    """
    if request.method == 'POST':
        try:
            client = utils.get_client()
            client.delete_domain(domain)
            messages.success(request,
                             _('The domain %s has been deleted.' % domain))
            return redirect("domain_index")
        except HTTPError as e:
            messages.error(request, _('The domain could not be deleted:'
                                      ' %s' % e.msg))
            return redirect("domain_index")
    submit_url = reverse('domain_delete',
                         kwargs={'domain': domain})
    return render_to_response('postorius/domain_confirm_delete.html',
                              {'domain': domain, 'submit_url': submit_url},
                              context_instance=RequestContext(request))
