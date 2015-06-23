﻿# -*- coding: utf-8 -*-
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
import collections
import json
import logging
from datetime import datetime, timedelta, date
from django.forms.formsets import formset_factory
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import (login_required,
                                            user_passes_test)
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django.http import HttpResponse
from urllib2 import HTTPError
from operator import itemgetter
from postorius import utils
from postorius.models import (
    MailmanUser, MailmanConnectionError, MailmanApiError, Mailman404Error,
    AddressConfirmationProfile, AdminTasks, Domain, List, EventTracker, TaskCalender)
from postorius.forms import *
from postorius.auth.decorators import *
from postorius.views.generic import MailmanUserView
from smtplib import SMTPException


class UserMailmanSettingsView(MailmanUserView):
    """The logged-in user's global Mailman Preferences."""

    @method_decorator(login_required)
    def post(self, request):
        try:
            mm_user = MailmanUser.objects.get(address=request.user.email)
            global_preferences_form = UserPreferences(request.POST)
            if global_preferences_form.is_valid():
                preferences = mm_user.preferences
                for key in global_preferences_form.fields.keys():
                    preferences[
                        key] = global_preferences_form.cleaned_data[key]
                    preferences.save()
                messages.success(
                    request, 'Your preferences have been updated.')
            else:
                messages.error(request, 'Something went wrong.')
        except MailmanApiError:
            return utils.render_api_error(request)
        except Mailman404Error as e:
            messages.error(request, e.msg)
        return redirect("user_mailmansettings")

    @method_decorator(login_required)
    def get(self, request):
        try:
            mm_user = MailmanUser.objects.get(address=request.user.email)
            settingsform = UserPreferences(initial=mm_user.preferences)
        except MailmanApiError:
            return utils.render_api_error(request)
        except Mailman404Error:
            mm_user = None
            settingsform = None
        return render_to_response('postorius/user_mailmansettings.html',
                                  {'mm_user': mm_user,
                                   'settingsform': settingsform},
                                  context_instance=RequestContext(request))


class UserAddressPreferencesView(MailmanUserView):
    """The logged-in user's address-based Mailman Preferences."""

    @method_decorator(login_required)
    def post(self, request):
        try:
            mm_user = MailmanUser.objects.get(address=request.user.email)
            formset_class = formset_factory(UserPreferences)
            formset = formset_class(request.POST)
            zipped_data = zip(formset.forms, mm_user.addresses)
            if formset.is_valid():
                for form, address in zipped_data:
                    preferences = address.preferences
                    for key in form.fields.keys():
                        preferences[
                            key] = form.cleaned_data[key]
                        preferences.save()
                messages.success(
                    request, 'Your preferences have been updated.')
            else:
                messages.error(request, 'Something went wrong.')
        except MailmanApiError:
            return utils.render_api_error(request)
        except HTTPError, e:
            messages.error(request, e.msg)
        return redirect("user_address_preferences")

    @method_decorator(login_required)
    def get(self, request):
        try:
            helperform = UserPreferences()
            mm_user = MailmanUser.objects.get(address=request.user.email)
            addresses = mm_user.addresses
            i = 0
            for address in addresses:
                i = i + 1
            AFormset = formset_factory(UserPreferences, extra=i)
            formset = AFormset()
            zipped_data = zip(formset.forms, addresses)
            for form, address in zipped_data:
                form.initial = address.preferences
        except MailmanApiError:
            return utils.render_api_error(request)
        except Mailman404Error:
            return render_to_response(
                'postorius/user_address_preferences.html',
                {'nolists': 'true'},
                context_instance=RequestContext(request))
        return render_to_response('postorius/user_address_preferences.html',
                                  {'mm_user': mm_user,
                                   'addresses': addresses,
                                   'helperform': helperform,
                                   'formset': formset,
                                   'zipped_data': zipped_data},
                                  context_instance=RequestContext(request))


class UserSubscriptionPreferencesView(MailmanUserView):
    """The logged-in user's subscription-based Mailman Preferences."""

    @method_decorator(login_required)
    def post(self, request):
        try:
            mm_user = MailmanUser.objects.get(address=request.user.email)
            formset_class = formset_factory(UserPreferences)
            formset = formset_class(request.POST)
            zipped_data = zip(formset.forms, mm_user.subscriptions)
            if formset.is_valid():
                for form, subscription in zipped_data:
                    preferences = subscription.preferences
                    for key in form.cleaned_data.keys():
                        preferences[key] = form.cleaned_data[key]
                    preferences.save()
                messages.success(
                    request, 'Your preferences have been updated.')
            else:
                messages.error(request, 'Something went wrong.')
        except MailmanApiError:
            return utils.render_api_error(request)
        except HTTPError, e:
            messages.error(request, e.msg)
        return redirect("user_subscription_preferences")

    @method_decorator(login_required)
    def get(self, request):
        try:
            mm_user = MailmanUser.objects.get(address=request.user.email)
            subscriptions = mm_user.subscriptions
            i = len(subscriptions)
            member_subscriptions = []
            for subscription in subscriptions:
                if subscription.role == "member":
                    member_subscriptions.append(subscription)
            Mformset = formset_factory(UserPreferences, extra=i)
            formset = Mformset()
            zipped_data = zip(formset.forms, member_subscriptions)
            for form, subscription in zipped_data:
                form.initial = subscription.preferences
        except MailmanApiError:
            return utils.render_api_error(request)
        except Mailman404Error:
            return render_to_response(
                'postorius/user_subscription_preferences.html',
                {'nolists': 'true'},
                context_instance=RequestContext(request))
        return render_to_response(
            'postorius/user_subscription_preferences.html',
            {'mm_user': mm_user,
             'subscriptions': subscriptions,
             'zipped_data': zipped_data,
             'formset': formset},
            context_instance=RequestContext(request))


class UserSummaryView(MailmanUserView):

    """Shows a summary of a user.
    """

    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def get(self, request, user_id):
        settingsform = MembershipSettings()
        memberships = self._get_memberships()
        return render_to_response('postorius/users/summary.html',
                                  {'mm_user': self.mm_user,
                                   'settingsform': settingsform,
                                   'memberships': memberships},
                                  context_instance=RequestContext(request))


class UserSubscriptionsView(MailmanUserView):

    """Shows the subscriptions of a user.
    """

    def get(self, request):
        memberships = self._get_memberships()
        return render_to_response('postorius/user_subscriptions.html',
                                  {'memberships': memberships},
                                  context_instance=RequestContext(request))


class AddressActivationView(TemplateView):
    """
    Starts the process of adding additional email addresses to a mailman user 
    record. Forms are processes and email notifications are sent accordingly.
    """

    @method_decorator(login_required)
    def get(self, request):
        form = AddressActivationForm(initial={'user_email': request.user.email})
        return render_to_response('postorius/user_address_activation.html',
                                  {'form': form},
                                  context_instance=RequestContext(request))

    @method_decorator(login_required)
    def post(self, request):
        form = AddressActivationForm(request.POST)
        if form.is_valid():
            profile = AddressConfirmationProfile.objects.create_profile(
                email=form.cleaned_data['email'], user=request.user)
            try:
                profile.send_confirmation_link(request)
            except SMTPException:
                messages.error(request, 'The email confirmation message could '
                               'not be sent. %s' % profile.activation_key)
            return render_to_response('postorius/user_address_activation_sent.html',
                                      context_instance=RequestContext(request))
        return render_to_response('postorius/user_address_activation.html',
                                  {'form': form},
                                  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def user_index(request, page=1, template='postorius/users/index.html'):
    """Show a table of all users.
    """
    page = int(page)
    error = None
    try:
        mm_user_page = utils.get_client().get_user_page(25, page)
    except MailmanApiError:
        return utils.render_api_error(request)
    return render_to_response(
        template,
        {'error': error,
         'mm_user_page': mm_user_page,
         'mm_user_page_nr': page,
         'mm_user_page_previous_nr': page - 1,
         'mm_user_page_next_nr': page + 1,
         'mm_user_page_show_next': len(mm_user_page) >= 25},
        context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
def user_new(request):
    message = None
    if request.method == 'POST':
        form = UserNew(request.POST)
        if form.is_valid():
            user = MailmanUser(display_name=form.cleaned_data['display_name'],
                               email=form.cleaned_data['email'],
                               password=form.cleaned_data['password'])
            try:
                user.save()
            except MailmanApiError:
                return utils.render_api_error(request)
            except HTTPError, e:
                messages.error(request, e)
            else:
                messages.success(request, _("New User registered"))
            return redirect("user_index")
    else:
        form = UserNew()
    return render_to_response('postorius/users/new.html',
                              {'form': form, 'message': message},
                              context_instance=RequestContext(request))


def user_logout(request):
    logout(request)
    return redirect('user_login')


@login_required()
def user_profile(request, user_email=None):
    if not request.user.is_authenticated():
        return redirect('user_login')
    # try:
    #    the_user = User.objects.get(email=user_email)
    # except MailmanApiError:
    #    return utils.render_api_error(request)
    return render_to_response('postorius/user_profile.html',
                              # {'mm_user': the_user},
                              context_instance=RequestContext(request))

class pseudo_log(object):
    def __init__(self, date, log_type, log_num):
        self.on_date = date
        self.log_number = log_num
        self.log_type = log_type
        self.list_id = ""

class AdminTasksView(MailmanUserView):
    
    def get_timediff(self, admin_task):
        time_now = datetime.now()
        diff = time_now - admin_task.made_on
        if diff.days < 0:
            return ''
        elif diff.days == 0:
            if diff.seconds < 10:
                return "Just Now"
            if diff.seconds < 60:
                return str(diff.seconds) + " seconds ago"
            if diff.seconds < 120:
               return "a minute ago"
            if diff.seconds < 3600:
               return str(diff.seconds / 60) + " minutes ago"
            if diff.seconds < 7200:
               return "an hour ago"
            if diff.seconds < 86400:
               return str(diff.seconds / 3600) + " hours ago"
        if diff.days == 1:
            return "Yesterday"
        if diff.days < 7:
            return str(diff.days) + " days ago"
        return str(diff.days / 7) + " weeks ago"

    @method_decorator(login_required)
    def get(self, request):
        email = request.user.email
        lists = List.objects.all()
        mod_req = [dict(each_mod,list_id=each_list.fqdn_listname) for each_list in lists for each_mod in each_list.held]
        mod_req = sorted(mod_req, key=itemgetter('hold_date'), reverse=False)
        sub_req = [each_req for each_list in lists for each_req in each_list.requests]
        sub_req = sorted(sub_req, key=itemgetter('request_date'), reverse=False)
        mod_sync = AdminTasks.objects.get_count('moderation')
        sub_sync = AdminTasks.objects.get_count('subscription')
        for mod in mod_req[mod_sync:]:
            admin_task = AdminTasks.objects.create_task(
                task_id = mod['request_id'],
                task_type = 'moderation',
                stamp = mod['hold_date'],
                list_id = '.'.join(mod['list_id'].split('@')),
                user_email = mod['sender'])
            date = datetime.strptime(admin_task.made_on,'%Y-%m-%dT%H:%M:%S.%f').date()
            try:
                current_log = TaskCalender.objects.filter(on_date=date).filter(log_type='moderation').get(list_id=admin_task.list_id)
                current_log.log_number = current_log.log_number + 1
                current_log.save()
            except ObjectDoesNotExist as e:
                TaskCalender.objects.create_log(on_date=date, list_id=admin_task.list_id, log_type='moderation', log_number=1)
        for sub in sub_req[sub_sync:]:
            admin_req = AdminTasks.objects.create_task(
                task_id = sub['token'],
                task_type = 'subscription',
                stamp = sub['request_date'],
                list_id = sub['list_id'],
                user_email = sub['email'])
            date = datetime.strptime(admin_req.made_on,'%Y-%m-%dT%H:%M:%S').date()
            try:
                current_log = TaskCalender.objects.filter(on_date=date).filter(log_type='subscription').get(list_id=admin_req.list_id)
                current_log.log_number = current_log.log_number + 1
                current_log.save()
            except ObjectDoesNotExist as e:
                TaskCalender.objects.create_log(on_date=date, list_id=admin_req.list_id, log_type='subscription', log_number=1)
        tasks = AdminTasks.objects.all().order_by('priority').reverse()
        id_list = [list_mod['request_id'] for list_mod in mod_req] + [list_sub['token'] for list_sub in sub_req]
        for task in tasks:
            if task.task_type != 'manual' and task.task_id not in map(str,id_list):
                AdminTasks.objects.filter(task_id=task.task_id).delete()
        tasks = AdminTasks.objects.all().order_by('priority').reverse()
        tasks = filter_tasks_by_role(request.user, tasks, lists)
        lists = allowed_lists(request.user, lists)

        sub_objects, mod_objects = generate_graph_object([str(each_list.list_id) for each_list in lists])
        stats = {'subs': sub_objects, 'mods': mod_objects}
        for each in tasks:
            each.made_on = self.get_timediff(each)
        search_form = TaskSearchForm()
        search_li = ListIndexSearchForm()
        global_search = GlobalSearchForm()
        mtask_form = NewManualTaskForm()
        events = events_allowed(request.user, EventTracker.objects.all())
        for each in events:
            each.made_on = self.get_timediff(each)
            each.event_on = each.event_on.date()
        return render_to_response('postorius/user_dashboard.html',
                                  {'tasks': tasks, 'lists': lists, 'li_res': lists, 'mtask_form': mtask_form, 'search_li': search_li, 'search_form': search_form, 'global_search': global_search, 'events': events, 'stats': stats},
                                  context_instance=RequestContext(request))
    def post(self, request):
        tasks = AdminTasks.objects.all()
        lists = List().objects.all()
        email = request.user.email
        tasks = filter_tasks_by_role(request.user, tasks, lists)  
        lists = allowed_lists(request.user, lists)
        for each in tasks:
            each.made_on = self.get_timediff(each)
        if 'search_tasks' in request.POST:
            search_form = TaskSearchForm(request.POST)
            if search_form.is_valid():
                query = request.POST['search_tasks'].lower()
                if query.find("moderation") >= 0:
                        res = [each_task for each_task in tasks if each_task.task_type == 'moderation']
                elif query.find("subscription") >= 0:
                        res = [each_task for each_task in tasks if each_task.task_type == 'subscription']
                elif query.find("manual") >= 0 or query.find("self") >= 0 or query.find("reminder") >= 0:
                        res = [each_task for each_task in tasks if each_task.task_type == 'manual']
                elif query.find("priority") >= 0:
                    if query.find("high") >= 0:
                        res = [each_task for each_task in tasks if each_task.priority == 1]
                    elif query.find("medium") >= 0:
                        res = [each_task for each_task in tasks if each_task.priority == 0]
                    elif query.find("low") >= 0:
                        res = [each_task for each_task in tasks if each_task.priority == -1]
                    else:
                        res = [each_task for each_task in tasks if each_task.priority == -2]
                else:
                    res = [each_task for each_task in tasks if each_task.user_email.find(query) != -1]
        if 'search_li'in request.POST:
            search_li = ListIndexSearchForm(request.POST)
            if search_li.is_valid():
                li_query = request.POST['search_li'].lower()
                li_res = [each_list for each_list in lists if each_list.list_id.lower().find(li_query) >= 0]
        if 'query_field' in request.POST:
            query = request.POST.get('query_field').lower()
            global_result = {}
            if 'check_lists' in request.POST:
                lists_res = [ { "display_name": each.display_name, "list_id": each.list_id} for each in lists if each.list_id.find(query) >= 0]
                global_result['lists'] = lists_res
            if 'check_domains' in request.POST:
                domains_res = [{"mail_host": each.mail_host, "base_url": each.base_url} for each in Domain.objects.all() if each.mail_host.find(query) >=0]
                global_result['domains'] = domains_res
            if 'check_people' in request.POST:
                people_res = [{ "useremail": each_member.email, "list_id": each_list.list_id} for each_list in lists for each_member in each_list.members if each_member.email.find(query) >=0]
                global_result['people'] = people_res
            try:
                return HttpResponse(json.dumps(global_result), content_type="application/json")
            except Exception as e:
                print e
        if 'selected_lists[]' in request.POST:
            try:
                selects = request.POST.getlist('selected_lists[]')
                selects = [str(each) for each in selects]
                sub_objects, mod_objects = generate_graph_object(selects)
                return HttpResponse(json.dumps({'subs': sub_objects, 'mods': mod_objects}), content_type="application/json")
            except Exception as e:
                print e
        if 'mtask_subject' in request.POST:
            mtask_form = NewManualTaskForm(request.POST)
            if mtask_form.is_valid():
                mtask_subject = request.POST.get('mtask_subject')
                mtask_description = request.POST.get('mtask_description')
                try:
                    mtask_id = int(AdminTasks.objects.filter(task_type='manual').latest('made_on').task_id) -1
                except ObjectDoesNotExist:  
                    mtask_id = -1
                mtask = AdminTasks.objects.create_task(
                    task_id = mtask_id,
                    task_type = 'manual',
                    stamp = datetime.now(),
                    list_id = "",
                    user_email = request.user.email)
                mtask.msg_subject = mtask_subject
                mtask.msg_data = mtask_description
                mtask.save()
                tasks = AdminTasks.objects.all()
                tasks = filter_tasks_by_role(request.user, tasks, lists)  
                for each in tasks:
                    each.made_on = self.get_timediff(each)
            else:
                messages.error(request,
                            _('Error Creating Task entry : Task Heading can\'t be left Empty'))
                return redirect('user_dashboard')
        mtask_form = NewManualTaskForm()
        search_form = TaskSearchForm()
        search_li = ListIndexSearchForm()
        global_search = GlobalSearchForm()
        events = events_allowed(request.user, EventTracker.objects.all())
        try:
            stats
        except UnboundLocalError as e:
            sub_objects, mod_objects = generate_graph_object([each_list.list_id for each_list in lists])
            stats = {'subs': sub_objects, 'mods': mod_objects}
        for each in events:
            each.made_on = self.get_timediff(each)
            each.event_on = each.event_on.date()
        try:
            res
        except UnboundLocalError as e:
            res = tasks
        try:
            li_res
        except UnboundLocalError as e:
            li_res = lists
        return render_to_response('postorius/user_dashboard.html',
                                  {'tasks': res, 'lists': lists, 'li_res': li_res, 'mtask_form': mtask_form, 'search_li': search_li, 'search_form': search_form, 'global_search': global_search, 'events':events, 'stats': stats},
                                  context_instance=RequestContext(request))
        
def allowed_lists(user, lists):
    if not user.is_superuser:
        lists = [each for each in lists if user.email in each.owners or user.email in each.moderators]  
    return lists

def action_allowed(user, action, list_id):
    email = user.email
    the_list = List.objects.get(fqdn_listname=list_id)
    if user.is_superuser:
        return True
    if action == 'moderation':
        if email in the_list.moderators:
            return True
        return False
    elif action == 'subscription':
        if email in the_list.owners:
            return True
        return False

def events_allowed(user, events):
    allowed = []
    lists = List.objects.all()
    is_owner = len([each for each in lists if user.email in each.owners]) != 0
    is_moderator = len([each for each in lists if user.email in each.moderators]) != 0
    if not user.is_superuser:
        for each_event in events:
            if each_event.event.find('moderation') >= 0 and is_moderator:
                allowed.append(each_event)
            elif each_event.event.find('subscription') >= 0 and is_owner:
                allowed.append(each_event)
        return allowed
    else:
        return events

def generate_graph_object(select_lists):
    sub_objects = {}
    mod_objects = {}
    today = datetime.today().date()
    dates = []
    for i in range(0,31):
        dates.append(today + timedelta(days=-i))
    for date in dates:
        mod_count = TaskCalender.objects.filter(list_id__in=select_lists).filter(log_type="moderation").filter(on_date=date).count()
        sub_count = TaskCalender.objects.filter(list_id__in=select_lists).filter(log_type="subscription").filter(on_date=date).count()
        if mod_count == 0:
            mod_objects[date.strftime("%Y-%m-%d")] = 0
	elif mod_count > 0:
            mod_objects[date.strftime("%Y-%m-%d")] = mod_count
        if sub_count == 0:
            sub_objects[date.strftime("%Y-%m-%d")] = 0
        elif sub_count > 0:
            sub_objects[date.strftime("%Y-%m-%d")] = sub_count
    sub_objects = collections.OrderedDict(sorted(sub_objects.items()))
    mod_objects = collections.OrderedDict(sorted(mod_objects.items()))
    return sub_objects, mod_objects

@login_required
def set_task_priority(request, task_id, priority):
    """Set Priority for a Task."""
    try:
        the_task = AdminTasks.objects.get(task_id=task_id)
        if the_task.priority == int(priority):
            the_task.priority = -2
        else:
            the_task.priority = priority
        the_task.save()
        return redirect ('user_dashboard')
    except MailmanApiError:
        return utils.render_api_error(request)
    return redirect ('user_dashboard')

def filter_tasks_by_role(user, tasks, lists):
    user_manual_tasks = [each for each in tasks if each.user_email == user.email and each.task_type == 'manual']
    if not user.is_superuser:
        user_sub_tasks = [each for each in tasks if each.task_type == 'subscription' and user.email in List.objects.get(fqdn_listname=each.list_id).owners] 
        user_mod_tasks = [each for each in tasks if each.task_type == 'moderation' and (user.email in List.objects.get(fqdn_listname=each.list_id).moderators or user.email in List.objects.get(fqdn_listname=each.list_id).owners)]
        return user_sub_tasks + user_mod_tasks + user_manual_tasks
    return list(tasks.filter(~Q(task_type='manual'))) + user_manual_tasks
       
@login_required
def reorder_tasks_by(request, reorder_param):
    """Reorder Dashboard Tasks by specified parameter."""
    try:
        tasks = AdminTasks.objects.all().order_by(reorder_param).reverse()
        email = request.user.email
        lists = List.objects.all()
	global_search = GlobalSearchForm()
        search_form = TaskSearchForm()
        search_li = ListIndexSearchForm()
        mtask_form = NewManualTaskForm()
        events = events_allowed(request.user, EventTracker.objects.all())
        
        sub_objects, mod_objects = generate_graph_object([each_list.list_id for each_list in lists])
        stats = {'subs': sub_objects, 'mods': mod_objects}
        
        tasks = filter_tasks_by_role(request.user, tasks, lists)
        lists = allowed_lists(request.user, lists)
        for each in events:
            each.made_on = AdminTasksView().get_timediff(each)
            each.event_on = each.event_on.date()
        for each in tasks:
            each.made_on = AdminTasksView().get_timediff(each)
        return render_to_response('postorius/user_dashboard.html',
                                  {'tasks': tasks, 'lists': lists, 'li_res': lists, 'mtask_form': mtask_form, 'search_li': search_li, 'search_form': search_form, 'global_search': global_search, 'events':events, 'stats': stats},
                                  context_instance=RequestContext(request))
    except MailmanApiError:
        return utils.render_api_error(request)
    return render_to_response('postorius/user_dashboard.html',
                              {'tasks': tasks, 'lists': lists, 'li_res': lists, 'mtask_form': mtask_form, 'search_li': search_li, 'search_form': search_form, 'global_search': global_search, 'events':events, 'stats': stats},
                              context_instance=RequestContext(request))

@login_required
def discard_manual_task(request, task_id):
    """Discard The Manual Task Created By User"""

    try:
        mtask = AdminTasks.objects.get(task_id=task_id)
        if request.user.email != mtask.user_email:
            messages.error(request,
                          _('You Are Not Allowed To Perform This Operation'))
            return redirect('user_dashboard')
        mtask.delete()
    except ObjectDoesNotExist:
        messages.error(request,
                       _('The task with request id Does Not Exist'))
    return redirect('user_dashboard')

@login_required
def remove_role_tasks(request, list_id, role, email):
    """Remove Role from Lists, Redirect to dashboard."""
    try:
        the_list = List.objects.get_or_404(fqdn_listname=list_id)
        if role == 'owner':
            if email not in the_list.owners:
                messages.error(request,
                              _('The user {} is not an owner'.format(email)))
                return redirect('user_dashboard')
            the_list.remove_role(role, email)
        elif role == 'moderator':
            if email not in the_list.moderators:
                messages.error(request,
                              _('The user {} is not a moderator'.format(email)))
                return redirect('user_dashboard')
            the_list.remove_role(role, email)
        elif role == 'subscriber':
            the_list.unsubscribe(email)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError as e:
        messages.error(request, _('The {0} could not be removed:'
                                ' {1}'.format(role, e.msg)))
    return redirect('user_dashboard')

@user_passes_test(lambda u: u.is_superuser)
def user_delete(request, user_id,
                template='postorius/users/user_confirm_delete.html'):
    """ Deletes a user upon confirmation.
    """
    try:
        mm_user = MailmanUser.objects.get_or_404(address=user_id)
        email_id = mm_user.addresses[0]
    except MailmanApiError:
        return utils.render_api_error(request)
    except IndexError:
        email_id = ''
    if request.method == 'POST':
        try:
            mm_user.delete()
        except MailmanApiError:
            return utils.render_api_error(request)
        except HTTPError as e:
            messages.error(request, _('The user could not be deleted:'
                                      ' %s' % e.msg))
            return redirect("user_index")
        messages.success(request,
                         _('The user %s has been deleted.' % email_id))
        return redirect("user_index")
    return render_to_response(template,
                              {'user_id': user_id, 'email_id': email_id},
                              context_instance=RequestContext(request))


def _add_address(request, user_email, address):
    # Add an address to a user record in mailman.
    try:
        mailman_user = utils.get_client().get_user(user_email)
        mailman_user.add_address(address)
    except (MailmanApiError, MailmanConnectionError) as e:
        messages.error(request, 'The address could not be added.')


def address_activation_link(request, activation_key):
    """
    Checks the given activation_key. If it is valid, the saved address will be
    added to mailman. Also, the corresponding profile record will be removed. 
    If the key is not valid, it will be ignored. 
    """
    try:
        profile = AddressConfirmationProfile.objects.get(
            activation_key=activation_key)
        if not profile.is_expired:
            _add_address(request, profile.user.email, profile.email)
    except profile.DoesNotExist:
        pass
    return render_to_response('postorius/user_address_activation_link.html',
        {}, context_instance=RequestContext(request))
