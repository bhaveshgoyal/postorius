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
import csv

from django.http import HttpResponse

from django.contrib import messages
from django.contrib.auth.decorators import (login_required,
                                            user_passes_test)
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from urllib2 import HTTPError
from datetime import datetime
from postorius import utils
from postorius.models import (Domain, List, MailmanApiError, AdminTasks, EventTracker)
from postorius.forms import *
from postorius.auth.decorators import *
from postorius.views.generic import MailingListView


logger = logging.getLogger(__name__)


class ListMembersView(MailingListView):

    """Display all members of a given list.
    """

    def _get_list(self, list_id, page):
        m_list = super(ListMembersView, self)._get_list(list_id, page)
        m_list.member_page = m_list.get_member_page(25, page)
        m_list.member_page_nr = page
        m_list.member_page_previous_nr = page - 1
        m_list.member_page_next_nr = page + 1
        m_list.member_page_show_next = len(m_list.member_page) >= 25
        return m_list

    @method_decorator(list_owner_required)
    def post(self, request, list_id, page=1):
        if 'owner_email' in request.POST:
            owner_form = NewOwnerForm(request.POST)
            if owner_form.is_valid():
                try:
                    self.mailing_list.add_owner(
                        owner_form.cleaned_data['owner_email'])
                    messages.success(
                        request, _('%s has been added as list owner.'
                                   % request.POST['owner_email']))
                except HTTPError as e:
                    messages.error(request, _(e.msg))
        if 'moderator_email' in request.POST:
            moderator_form = NewModeratorForm(request.POST)
            if moderator_form.is_valid():
                try:
                    self.mailing_list.add_moderator(
                        moderator_form.cleaned_data['moderator_email'])
                    messages.success(
                        request, _('%s has been added as list moderator.'
                                   % request.POST['moderator_email']))
                except HTTPError as e:
                    messages.error(request, _(e.msg))
        owner_form = NewOwnerForm()
        moderator_form = NewModeratorForm()
        return render_to_response('postorius/lists/members.html',
                                  {'list': self.mailing_list,
                                   'owner_form': owner_form,
                                   'moderator_form': moderator_form},
                                  context_instance=RequestContext(request))

    @method_decorator(list_owner_required)
    def get(self, request, list_id, page=1):
        owner_form = NewOwnerForm()
        moderator_form = NewModeratorForm()
        return render_to_response('postorius/lists/members.html',
                                  {'list': self.mailing_list,
                                   'owner_form': owner_form,
                                   'moderator_form': moderator_form},
                                  context_instance=RequestContext(request))


class ListMemberOptionsView(MailingListView):
    '''View the preferences for a single member of a mailing list'''

    @method_decorator(list_owner_required)
    def post(self, request, list_id, email):
        try:
            client = utils.get_client()
            mm_member = client.get_member(list_id, email)
            mm_list = client.get_list(list_id)
            preferences_form = UserPreferences(request.POST)
            if preferences_form.is_valid():
                preferences = mm_member.preferences
                for key in preferences_form.fields.keys():
                    preferences[key] = preferences_form.cleaned_data[key]
                preferences.save()
                messages.success(
                    request, 'The member\'s preferences have been updated.')
            else:
                messages.error(request, 'Something went wrong.')

            # this is a bit silly, since we already have the preferences,
            # but I want to be sure we don't show stale data.
            settingsform = UserPreferences(initial=mm_member.preferences)
        except MailmanApiError:
            return utils.render_api_error(request)
        except HTTPError, e:
            messages.error(request, e.msg)
        return render_to_response(
            'postorius/lists/memberoptions.html',
            {'mm_member': mm_member,
             'list': mm_list,
             'settingsform': settingsform,
             },
            context_instance=RequestContext(request))

    @method_decorator(list_owner_required)
    def get(self, request, list_id, email):
        try:
            client = utils.get_client()
            mm_member = client.get_member(list_id, email)
            mm_list = client.get_list(list_id)
            settingsform = UserPreferences(initial=mm_member.preferences)
        except MailmanApiError:
            return utils.render_api_error(request)
        except Mailman404Error:
            return render_to_response(
                'postorius/lists/memberoptions.html',
                {'nolists': 'true'},
                context_instance=RequestContext(request))
        return render_to_response(
            'postorius/lists/memberoptions.html',
            {'mm_member': mm_member,
             'list': mm_list,
             'settingsform': settingsform,
             },
            context_instance=RequestContext(request))


class ListMetricsView(MailingListView):

    """Shows common list metrics.
    """

    @method_decorator(list_owner_required)
    def get(self, request, list_id):
        return render_to_response('postorius/lists/metrics.html',
                                  {'list': self.mailing_list},
                                  context_instance=RequestContext(request))


class ListSummaryView(MailingListView):
    """Shows common list metrics.
    """

    def get(self, request, list_id):
        try:
            mm_user = MailmanUser.objects.get(address=request.user.email)
            user_emails = [str(address) for address in getattr(mm_user, 'addresses')]
            # TODO:maxking - add the clause below in above
            # statement after the subscription policy is sorted out
            # if address.verified_on is not None]
        except Mailman404Error:
            # The user does not have a mailman user associated with it.
            user_emails = [request.user.email]
        except AttributeError:
            # Anonymous User, everyone logged out.
            user_emails = None

        userSubscribed = False
        subscribed_address = None
        if user_emails is not None:
            for address in user_emails:
                try:
                    userMember = self.mailing_list.get_member(address)
                except ValueError:
                    pass
                else:
                    userSubscribed = True
                    subscribed_address = address
        data =  {'list': self.mailing_list,
                 'userSubscribed': userSubscribed,
                 'subscribed_address': subscribed_address}
        if user_emails is not None:
            data['change_subscription_form'] = ChangeSubscriptionForm(user_emails,
                                                 initial={'email': subscribed_address})
            data['subscribe_form'] = ListSubscribe(user_emails)
        else:
            data['change_subscription_form'] = None
        return render_to_response(
            'postorius/lists/summary.html', data,
            context_instance=RequestContext(request))

class ChangeSubscriptionView(MailingListView):
    """Change mailing list subscription
    """

    @method_decorator(login_required)
    def post(self, request, list_id):
        try:
            mm_user = MailmanUser.objects.get(address=request.user.email)
            user_emails = [str(address) for address in mm_user.addresses]
            form = ListSubscribe(user_emails, request.POST)
            for address in user_emails:
                try:
                    userMember = self.mailing_list.get_member(address)
                except ValueError:
                    pass
                else:
                    userSubscribed = True
                    old_email = address
            if form.is_valid():
                email = form.cleaned_data['email']
                if old_email == email:
                    messages.error(request, 'You are already subscribed')
                else:
                    self.mailing_list.unsubscribe(old_email)
                    self.mailing_list.subscribe(email)
                    messages.success(request,
                        'Subscription changed to {} address'.format(email))
            else:
                messages.error(request, 'Something went wrong. '
                               'Please try again.')
        except MailmanApiError:
            return utils.render_api_error(request)
        except HTTPError, e:
            messages.error(request, e.msg)
        return redirect('list_summary', self.mailing_list.list_id)

class ListSubscribeView(MailingListView):
    """
    view name: `list_subscribe`
    """

    @method_decorator(login_required)
    def post(self, request, list_id):
        """
        Subscribes an email address to a mailing list via POST and 
        redirects to the `list_summary` view.
        """
        try:
            try:
                mm_user = MailmanUser.objects.get(address=request.user.email)
                user_addresses = [str(address) for address in mm_user.addresses]
            except Mailman404Error:
                mm_user = None
                user_addresses = (request.POST.get('email'),)
            form = ListSubscribe(user_addresses, request.POST)
            if form.is_valid():
                email = request.POST.get('email')
                response = self.mailing_list.subscribe(
                    email, pre_verified=True, pre_confirmed=True)
                if type(response) == dict and response.get('token_owner') == \
                        'moderator':
                    messages.success(
                        request,
                        'Your subscription request has been submitted and is '
                        'waiting for moderator approval.')
                else:
                    messages.success(
                        request, 'You are subscribed to %s.' %
                        self.mailing_list.fqdn_listname)
            else:
                messages.error(request, 'Something went wrong. '
                               'Please try again.')
        except MailmanApiError:
            return utils.render_api_error(request)
        except HTTPError, e:
            messages.error(request, e.msg)
        return redirect('list_summary', self.mailing_list.list_id)


class ListUnsubscribeView(MailingListView):

    """Unsubscribe from a mailing list."""

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        email = kwargs['email']
        try:
            self.mailing_list.unsubscribe(email)
            messages.success(request,
                             '%s has been unsubscribed from this list.' %
                             email)
        except MailmanApiError:
            return utils.render_api_error(request)
        except ValueError, e:
            messages.error(request, e)
        return redirect('list_summary', self.mailing_list.list_id)


class ListMassSubscribeView(MailingListView):
    """Mass subscription."""

    @method_decorator(list_owner_required)
    def get(self, request, *args, **kwargs):
        form = ListMassSubscription()
        return render_to_response('postorius/lists/mass_subscribe.html',
                                  {'form': form, 'list': self.mailing_list},
                                  context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        form = ListMassSubscription(request.POST)
        if not form.is_valid():
            messages.error(request, 'Please fill out the form correctly.')
        else:
            emails = request.POST["emails"].splitlines()
            for email in emails:
                try:
                    validate_email(email)
                    self.mailing_list.subscribe(address=email, pre_verified=True,
                                                pre_confirmed=True)
                    messages.success(
                        request,
                        'The address %s has been subscribed to %s.' %
                        (email, self.mailing_list.fqdn_listname))
                except MailmanApiError:
                    return utils.render_api_error(request)
                except HTTPError, e:
                    messages.error(request, e)
                except ValidationError:
                    messages.error(request,
                                   'The email address %s is not valid.' %
                                   email)
        return redirect('mass_subscribe', self.mailing_list.list_id)


class ListMassRemovalView(MailingListView):

    """Class For Mass Removal"""

    @method_decorator(list_owner_required)
    def get(self, request, *args, **kwargs):
        form = ListMassRemoval()
        return render_to_response('postorius/lists/mass_removal.html',
                                  {'form': form, 'list': self.mailing_list},
                                  context_instance=RequestContext(request))

    @method_decorator(list_owner_required)
    def post(self, request, *args, **kwargs):
        form = ListMassRemoval(request.POST)
        if not form.is_valid():
            messages.error(request, 'Please fill out the form correctly.')
        else:
            emails = request.POST["emails"].splitlines()
            for email in emails:
                try:
                    validate_email(email)
                    self.mailing_list.unsubscribe(email.lower())
                    messages.success(request,
                                    'The address %s has been unsubscribed from %s.' %
                                    (email, self.mailing_list.fqdn_listname))
                except MailmanApiError:
                    return utils.render_api_error(request)
                except HTTPError, e:
                    messages.error(request, e)
                except ValueError, e:
                    messages.error(request, e)
                except ValidationError:
                    messages.error(request,
                                  'The email address %s is not valid.' %
                                  email)
        return redirect('mass_removal', self.mailing_list.list_id)


@list_owner_required
def csv_view(request, list_id):
    """Export all the subscriber in csv
    """
    mm_lists = []
    try:
        client = utils.get_client()
        mm_lists = client.get_list(list_id)
    except MailmanApiError:
        return utils.render_api_error(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="Subscribers.csv"')

    writer = csv.writer(response)
    if mm_lists:
        for i in mm_lists.members:
            writer.writerow([i.email])

    return response


def _get_choosable_domains(request):
    try:
        domains = Domain.objects.all()
    except MailmanApiError:
        return utils.render_api_error(request)
    choosable_domains = [("", _("Choose a Domain"))]
    for domain in domains:
        choosable_domains.append((domain.mail_host,
                                  domain.mail_host))
    return choosable_domains


@login_required
@user_passes_test(lambda u: u.is_superuser)
def list_new(request, template='postorius/lists/new.html'):
    """
    Add a new mailing list.
    If the request to the function is a GET request an empty form for
    creating a new list will be displayed. If the request method is
    POST the form will be evaluated. If the form is considered
    correct the list gets created and otherwise the form with the data
    filled in before the last POST request is returned. The user must
    be logged in to create a new list.
    """
    mailing_list = None
    if request.method == 'POST':
        choosable_domains = _get_choosable_domains(request)
        form = ListNew(choosable_domains, request.POST)
        if form.is_valid():
            # grab domain
            domain = Domain.objects.get_or_404(
                mail_host=form.cleaned_data['mail_host'])
            # creating the list
            try:
                mailing_list = domain.create_list(
                    form.cleaned_data['listname'])
                mailing_list.add_owner(form.cleaned_data['list_owner'])
                list_settings = mailing_list.settings
                list_settings["description"] = form.cleaned_data['description']
                list_settings["advertised"] = form.cleaned_data['advertised']
                list_settings.save()
                messages.success(request, _("List created"))
                return redirect("list_summary",
                                list_id=mailing_list.list_id)
            # TODO catch correct Error class:
            except HTTPError, e:
                return render_to_response(
                    'postorius/errors/generic.html',
                    {'error': e}, context_instance=RequestContext(request))
            else:
                messages.success(_("New List created"))
    else:
        choosable_domains = _get_choosable_domains(request)
        form = ListNew(choosable_domains,
                       initial={'list_owner': request.user.email})
    return render_to_response(template, {'form': form},
                              context_instance=RequestContext(request))


def list_index(request, template='postorius/lists/index.html'):
    """Show a table of all public mailing lists.
    """
    lists = []
    error = None
    only_public = True
    if request.user.is_superuser:
        only_public = False
    try:
        lists = List.objects.all(only_public=only_public)
        logger.debug(lists)
    except MailmanApiError:
        return utils.render_api_error(request)
    choosable_domains = _get_choosable_domains(request)
    if request.method == 'POST':
        return redirect("list_summary", list_id=request.POST["list"])
    else:
        return render_to_response(template,
                                  {'error': error,
                                   'lists': lists,
                                   'domain_count': len(choosable_domains)},
                                  context_instance=RequestContext(request))


@login_required
def list_subscriptions(request, option=None, list_id=None,
                       user_email=None,
                       template='postorius/lists/subscriptions.html',
                       *args, **kwargs):
    """
    Display the information there is available for a list. This
    function also enables subscribing or unsubscribing a user to a
    list. For the latter two different forms are available for the
    user to fill in which are evaluated in this function.
    """
    # create Values for Template usage
    message = None
    error = None
    form_subscribe = None
    form_unsubscribe = None
    if request.POST.get('list_id', ''):
        list_id = request.POST.get('list_id', '')
    # connect REST and catch issues getting the list
    try:
        the_list = List.objects.get_or_404(fqdn_listname=list_id)
    except AttributeError, e:
        return render_to_response('postorius/errors/generic.html',
                                  {'error': 'Mailman REST API not available.'
                                   ' Please start Mailman core.'},
                                  context_instance=RequestContext(request))
    # process submitted form
    if request.method == 'POST':
        form = False
        # The form enables both subscribe and unsubscribe. As a result
        # we must find out which was the case.
        if request.POST.get('name', '') == "subscribe":
            form = ListSubscribe(request.POST)
            if form.is_valid():
                # the form was valid so try to subscribe the user
                try:
                    email = form.cleaned_data['email']
                    the_list.subscribe(
                        address=email,
                        display_name=form.cleaned_data.get('display_name', ''))
                    return render_to_response(
                        'postorius/lists/summary.html',
                        {'list': the_list, 'option': option,
                         'message': _("Subscribed ") + email},
                        context_instance=RequestContext(request))
                except HTTPError, e:
                    return render_to_response(
                        'postorius/errors/generic.html',
                        {'error': e},
                        context_instance=RequestContext(request))
            else:  # invalid subscribe form
                form_subscribe = form
                form_unsubscribe = ListUnsubscribe(
                    initial={'fqdn_listname': fqdn_listname,
                             'name': 'unsubscribe'})
        elif request.POST.get('name', '') == "unsubscribe":
            form = ListUnsubscribe(request.POST)
            if form.is_valid():
                # the form was valid so try to unsubscribe the user
                try:
                    email = form.cleaned_data["email"]
                    the_list.unsubscribe(address=email)
                    return render_to_response(
                        'postorius/lists/summary.html',
                        {'list': the_list,
                         'message': _("Unsubscribed ") + email},
                        context_instance=RequestContext(request))
                except ValueError, e:
                    return render_to_response(
                        'postorius/errors/generic.html',
                        {'error': e},
                        context_instance=RequestContext(request))
            else:  # invalid unsubscribe form
                form_subscribe = ListSubscribe(
                    initial={'fqdn_listname': fqdn_listname,
                             'option': option,
                             'name': 'subscribe'})
                form_unsubscribe = ListUnsubscribe(request.POST)
    else:
        # the request was a GET request so set the two forms to empty
        # forms
        if option == "subscribe" or not option:
            form_subscribe = ListSubscribe(
                initial={'fqdn_listname': fqdn_listname,
                         'email': request.user.username,
                         'name': 'subscribe'})
        if option == "unsubscribe" or not option:
            form_unsubscribe = ListUnsubscribe(
                initial={'fqdn_listname': fqdn_listname,
                         'email': request.user.username,
                         'name': 'unsubscribe'})
    the_list = List.objects.get_or_404(fqdn_listname=list_id)
    return render_to_response(template,
                              {'form_subscribe': form_subscribe,
                               'form_unsubscribe': form_unsubscribe,
                               'message': message,
                               'error': error,
                               'list': the_list},
                              context_instance=RequestContext(request))

def add_mod_event(request, msg_id, list_id, action):
    """Adds a Moderation Event Log For Event Tracker."""
    event_count = EventTracker.objects.get_count()
    if event_count == 30:
        EventTracker.objects.earliest('made_on').delete()
    the_list = List.objects.get_or_404(fqdn_listname=list_id)
    the_msg = next((each for each in the_list.held if each['request_id'] == int(msg_id)), None)
    event = 'moderation-' + action
    user_email = the_msg['sender']
    made_on = datetime.now()
    event_op = request.user.email
    event_logged = EventTracker.objects.create_event(
                    user_email=user_email,
                    event_op=event_op,
                    event=event,
                    list_id=list_id,
                    made_on=made_on)

def add_sub_event(request, sub_id, list_id, action):
    """Adds an Subscription Event Log For Event Tracker."""
    event_count = EventTracker.objects.get_count()
    if event_count == 30:
        EventTracker.objects.earliest('made_on').delete()
    the_list = List.objects.get_or_404(fqdn_listname=list_id)
    sub_req = next((each for each in the_list.requests if each['token'] == sub_id), None)
    event = 'subscription-' + action
    user_email = sub_req['email']
    made_on = datetime.now()
    event_op = request.user.email
    event_logged = EventTracker.objects.create_event(
                   user_email=user_email,
                   event_op=event_op,
                   event=event,
                   list_id=list_id,
                   made_on=made_on)

	
@list_owner_required
def list_delete(request, list_id):
    """Deletes a list but asks for confirmation first.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=list_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    if request.method == 'POST':
        the_list.delete()
        return redirect("list_index")
    else:
        submit_url = reverse('list_delete',
                             kwargs={'list_id': list_id})
        cancel_url = reverse('list_index',)
        return render_to_response(
            'postorius/lists/confirm_delete.html',
            {'submit_url': submit_url, 'cancel_url': cancel_url,
             'list': the_list},
            context_instance=RequestContext(request))


@list_moderator_required
def list_held_messages(request, list_id):
    """Shows a list of held messages.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=list_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    return render_to_response('postorius/lists/held_messages.html',
                              {'list': the_list},
                              context_instance=RequestContext(request))


@list_moderator_required
def accept_held_message(request, list_id, msg_id):
    """Accepts a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=list_id)
        add_mod_event(request, msg_id, list_id, 'accept')
        the_list.accept_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request, e.msg)
        return redirect('list_held_messages', the_list.list_id)
    messages.success(request, 'The message has been accepted.')
    return redirect('list_held_messages', the_list.list_id)


@list_moderator_required
def discard_held_message(request, list_id, msg_id):
    """Discards a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=list_id)
        add_mod_event(request, msg_id, list_id, 'discard')
        the_list.discard_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request, e.msg)
        return redirect('list_held_messages', the_list.list_id)
    messages.success(request, 'The message has been discarded.')
    return redirect('list_held_messages', the_list.list_id)


@list_moderator_required
def defer_held_message(request, list_id, msg_id):
    """Defers a held message for a later decision.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=list_id)
        add_mod_event(request, msg_id, list_id, 'defer')
        the_list.defer_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request, e.msg)
        return redirect('list_held_messages', the_list.list_id)
    messages.success(request, 'The message has been deferred.')
    return redirect('list_held_messages', the_list.list_id)


@list_moderator_required
def reject_held_message(request, list_id, msg_id):
    """Rejects a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=list_id)
        add_mod_event(request, msg_id, list_id, 'reject')
        the_list.reject_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request, e.msg)
        return redirect('list_held_messages', the_list.list_id)
    messages.success(request, 'The message has been rejected.')
    return redirect('list_held_messages', the_list.list_id)


@list_moderator_required
def list_subscription_requests(request, list_id):
    """Shows a list of held messages.
    """
    try:
        m_list = utils.get_client().get_list(list_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    return render_to_response('postorius/lists/subscription_requests.html',
                              {'list': m_list},
                              context_instance=RequestContext(request))


@list_moderator_required
def handle_subscription_request(request, list_id, request_id, action):
    """
    Handle a subscription request. Possible actions:
        - accept
        - defer
        - reject
        - discard
    """
    confirmation_messages = {
        'accept': _('The request has been accepted.'),
        'reject': _('The request has been rejected.'),
        'discard': _('The request has been discarded.'),
        'defer': _('The request has been defered.'),
    }
    try:
        m_list = utils.get_client().get_list(list_id)
        # Moderate request and add feedback message to session.
        add_sub_event(request, request_id, list_id, action)
        m_list.moderate_request(request_id, action)
        messages.success(request, confirmation_messages[action])
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError as e:
        messages.error(request, '{0}: {1}'.format(
            _('The request could not be moderated'), e.reason))
    return redirect('list_subscription_requests', m_list.list_id)


SETTINGS_SECTION_NAMES = (
    ('list_identity', _('List Identity')),
    ('automatic_responses', _('Automatic Responses')),
    ('alter_messages', _('Alter Messages')),
    ('digest', _('Digest')),
    ('message_acceptance', _('Message Acceptance')),
    ('archiving', _('Archiving')),
    ('subscription_policy', _('Subscription Policy')),
)

SETTINGS_FORMS = {
    'list_identity': ListIdentityForm,
    'automatic_responses': ListAutomaticResponsesForm,
    'alter_messages': AlterMessagesForm,
    'digest': DigestSettingsForm,
    'message_acceptance': MessageAcceptanceForm,
    'archiving': ArchivePolicySettingsForm,
    'subscription_policy': ListSubscriptionPolicyForm,
}


@list_owner_required
def list_settings(request, list_id=None, visible_section=None,
                  template='postorius/lists/settings.html'):
    """
    View and edit the settings of a list.
    The function requires the user to be logged in and have the
    permissions necessary to perform the action.

    Use /<NAMEOFTHESECTION>/<NAMEOFTHEOPTION>
    to show only parts of the settings
    <param> is optional / is used to differ in between section and option might
    result in using //option
    """
    message = ""
    if visible_section is None:
        visible_section = 'list_identity'
    form_class = SETTINGS_FORMS.get(visible_section)
    try:
        m_list = List.objects.get_or_404(fqdn_listname=list_id)
        list_settings = m_list.settings
    except MailmanApiError, HTTPError:
        return utils.render_api_error(request)
    # List settings are grouped an processed in different forms.
    if form_class:
        if request.method == 'POST':
            form = form_class(request.POST)
            if form.is_valid():
                try:
                    for key in form.fields.keys():
                        list_settings[key] = form.cleaned_data[key]
                    list_settings.save()
                    messages.success(request,
                                     _('The settings have been updated.'))
                except HTTPError as e:
                    messages.error(
                        request,
                        '{0}: {1}'.format(_('An error occured'), e.reason))
        else:
            form = form_class(initial=list_settings)

    return render_to_response(template,
                              {'form': form,
                               'section_names': SETTINGS_SECTION_NAMES,
                               'message': message,
                               'list': m_list,
                               'visible_section': visible_section},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def remove_role(request, list_id=None, role=None, address=None,
                template='postorius/lists/confirm_remove_role.html'):
    """Removes a list moderator or owner.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=list_id)
    except MailmanApiError:
        return utils.render_api_error(request)

    if role == 'owner':
        if address not in the_list.owners:
            messages.error(request,
                           _('The user {} is not an owner'.format(address)))
            return redirect("list_members", the_list.list_id)
    elif role == 'moderator':
        if address not in the_list.moderators:
            messages.error(request,
                           _('The user {} is not a moderator'.format(address)))
            return redirect("list_members", the_list.list_id)

    if request.method == 'POST':
        try:
            the_list.remove_role(role, address)
        except MailmanApiError:
            return utils.render_api_error(request)
        except HTTPError as e:
            messages.error(request, _('The {0} could not be removed:'
                                      ' {1}'.format(role, e.msg)))
            return redirect("list_members", the_list.list_id)
        messages.success(request,
                         _('The user {0} has been removed as {1}.'
                           .format(address, role)))
        return redirect("list_members", the_list.list_id)

    return render_to_response(template,
                              {'role': role, 'address': address,
                               'list_id': the_list.list_id},
                              context_instance=RequestContext(request))


def _add_archival_messages(to_activate, to_disable, after_submission,
                           request):
    """
    Add feedback messages to session, depending on previously set archivers.
    """
    # There are archivers to enable.
    if len(to_activate) > 0:
        # If the archiver shows up in the data set *after* the update,
        # we can show a success message.
        activation_postponed = []
        activation_success = []
        for archiver in to_activate:
            if after_submission[archiver] is True:
                activation_success.append(archiver)
            else:
                activation_postponed.append(archiver)
        # If archivers couldn't be updated, show a message:
        if len(activation_postponed) > 0:
            messages.warning(request,
                             _('Some archivers could not be enabled, probably '
                               'because they are not enabled in the Mailman '
                               'configuration. They will be enabled for '
                               'this list, if the archiver is enabled in the '
                               'Mailman configuration. {0}.'
                               ''.format(', '.join(activation_postponed))))
        if len(activation_success) > 0:
            messages.success(request,
                             _('You activated new archivers for this list: '
                               '{0}'.format(', '.join(activation_success))))
    # There are archivers to disable.
    if len(to_disable) > 0:
        messages.success(request,
                         _('You disabled the following archivers: '
                           '{0}'.format(', '.join(to_disable))))


@list_owner_required
def remove_all_subscribers(request, list_id):

    """Empty the list by unsubscribing all members."""

    try:
        mlist = List.objects.get_or_404(fqdn_listname=list_id)
        if len(mlist.members) == 0:
            messages.error(request, 'No member is subscribed to the list currently.')
            return redirect('mass_removal', mlist.list_id)
        if request.method == 'POST':
            try:
                for names in mlist.members:
                    mlist.unsubscribe(names.email)
                messages.success(request,
                                'All members have been unsubscribed from the list.')
                return redirect('list_members', mlist.list_id)
            except Exception, e:
                messages.error(request, e)
        return render_to_response('postorius/lists/confirm_removeall_subscribers.html',
                                 {'list_id': mlist.list_id},
                                 context_instance=RequestContext(request))
    except MailmanApiError:
        return utils.render_api_error(request)


@list_owner_required
def list_archival_options(request, list_id):
    """
    Activate or deactivate list archivers.
    """
    # Get the list and cache the archivers property.
    m_list = utils.get_client().get_list(list_id)
    archivers = m_list.archivers

    # Process form submission.
    if request.method == 'POST':
        current = [key for key in archivers.keys() if archivers[key]]
        posted = request.POST.getlist('archivers')

        # These should be activated
        to_activate = [arc for arc in posted if arc not in current]
        for arc in to_activate:
            archivers[arc] = True
        # These should be disabled
        to_disable = [arc for arc in current if arc not in posted and
                      arc in current]
        for arc in to_disable:
            archivers[arc] = False

        # Re-cache list of archivers after update.
        archivers = m_list.archivers

        # Show success/error messages.
        _add_archival_messages(to_activate, to_disable, archivers, request)

    # Instantiate form with current archiver data.
    initial = {'archivers': [key for key in archivers.keys()
                             if archivers[key] is True]}
    form = ListArchiverForm(initial=initial, archivers=archivers)

    return render_to_response('postorius/lists/archival_options.html',
                              {'list': m_list,
                               'form': form,
                               'archivers': archivers},
                              context_instance=RequestContext(request))

def task_delete(task_id):
        the_task = AdminTasks.objects.get(task_id=task_id)
        the_task.delete()

@list_moderator_required
def handle_mod_task(request, list_id, msg_id, action):
    """Handle Moderation Tasks On Dashboard.
    """

    response_messages = {
        'accept': _('The message has been accepted.'),
        'reject': _('The message has been rejected.'),
        'discard': _('The message has been discarded.'),
        'defer': _('The message has been deferred.'),
    }
    try:
        the_list = List.objects.get_or_404(fqdn_listname=list_id)
        method = 'the_list.' + action + '_message(msg_id)'
        add_mod_event(request, msg_id, list_id, action)
        eval(method)
        task_delete(msg_id)
        messages.success(request, response_messages[action])
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request, e.msg)
    return redirect('user_dashboard')

@list_moderator_required
def handle_sub_task(request, list_id, sub_id, action):
    """Handle Subscription Request Tasks on Dashboard.
    """
    
    response_messages = {
        'accept': _('The request has been accepted.'),
        'reject': _('The request has been rejected.'),
        'discard': _('The request has been discarded.'),
    }
    try:
        m_list = utils.get_client().get_list(list_id)
        add_sub_event(request, sub_id, list_id, action)
        m_list.moderate_request(sub_id, action)
        task_delete(sub_id)
        messages.success(request, response_messages[action])
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError as e:
        messages.error(request, e.msg)
    return redirect('user_dashboard')
