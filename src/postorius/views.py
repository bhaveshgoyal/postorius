# -*- coding: utf-8 -*-
# Copyright (C) 1998-2010 by the Free Software Foundation, Inc.
#
# This file is part of GNU Mailman.
#
# GNU Mailman is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# GNU Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# GNU Mailman.  If not, see <http://www.gnu.org/licenses/>.


import re
import sys
import utils
import logging


from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import (login_required, permission_required,
                                            user_passes_test)
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import Context, loader, RequestContext
from django.utils.translation import gettext as _
from mailman.client import Client
from models import (Domain, List, Member, MailmanUser, MailmanApiError,
                    Mailman404Error)
from forms import *
from urllib2 import HTTPError


logger = logging.getLogger(__name__)


@login_required
@permission_required('server_admin')
def site_settings(request):
    return render_to_response('mailmanweb/site_settings.html',
					          context_instance=RequestContext(request))

@login_required
@permission_required('server_admin')
def domain_index(request):
    try:
        existing_domains = Domain.objects.all()
    except MailmanApiError:
        return utils.render_api_error(request)
    return render_to_response('mailmanweb/domain_index.html', {'domains':existing_domains,},
					          context_instance=RequestContext(request))

@login_required
@permission_required('server_admin')
def domain_new(request):
    message = None
    if request.method == 'POST':
        form = DomainNew(request.POST)
        if form.is_valid():
            domain = Domain(mail_host=form.cleaned_data['mail_host'],
                            base_url=form.cleaned_data['web_host'],
                            description=form.cleaned_data['description'])
            try:
                domain.save()
            except MailmanApiError:
                return utils.render_api_error(request)
            except HTTPError, e:
                messages.error(request,e)
            else:
                messages.success(request,_("New Domain registered"))
            return redirect("domain_index")
    else:
        form = DomainNew()
    return render_to_response('mailmanweb/domain_new.html',
                              {'form': form,'message': message},
                              context_instance=RequestContext(request))

@login_required
def list_new(request, template = 'mailmanweb/lists/new.html'):
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
        try:
            domains = Domain.objects.all()
        except MailmanApiError:
            return utils.render_api_error(request)
        choosable_domains = [("",_("Choose a Domain"))]
        for domain in domains:
            choosable_domains.append((domain.mail_host,
                                      domain.mail_host))
        form = ListNew(choosable_domains, request.POST)
        if form.is_valid():
            #grab domain
            domain = Domain.objects.get_or_404(mail_host=form.cleaned_data['mail_host'])
            #creating the list
            try:
                mailing_list = domain.create_list(form.cleaned_data['listname'])
                list_settings = mailing_list.settings
                list_settings["description"] = form.cleaned_data['description']
                list_settings["owner_address"] = form.cleaned_data['list_owner']
                list_settings["advertised"] = form.cleaned_data['advertised']
                list_settings.save()
                messages.success(request, _("List created"))
                return redirect("list_summary",fqdn_listname=mailing_list.fqdn_listname)
            #TODO catch correct Error class:
            except HTTPError, e:
                messages.error(request,e)
                return render_to_response('mailmanweb/errors/generic.html', 
                                      {'error':e},
                                      context_instance=RequestContext(request))
            else:
                messages.success(_("New List created"))
    else:
        try:
            domains = Domain.objects.all()
        except MailmanApiError:
            return utils.render_api_error(request)
        choosable_domains = [("",_("Choose a Domain"))]
        for domain in domains:
            choosable_domains.append((domain.mail_host,domain.mail_host))
        form = ListNew(choosable_domains,initial={'list_owner': request.user.username})
    return render_to_response(template, {'form': form},
                              context_instance=RequestContext(request))

def list_index(request, template = 'mailmanweb/lists/index.html'):
    """Show a table of all public mailing lists.
    """
    lists = []
    error = None
    domain = None
    only_public = True
    if request.user.is_authenticated():
        only_public = False
    try:
        lists = List.objects.all(only_public=only_public)
    except MailmanApiError:
        return utils.render_api_error(request)
    if request.method == 'POST':
        return redirect("list_summary", fqdn_listname=request.POST["list"])
    else:
        return render_to_response(template,
                                  {'error': error,
                                   'lists': lists,},
                                  context_instance=RequestContext(request))

def list_metrics(request,fqdn_listname=None,option=None,template='mailmanweb/lists/metrics.html'):
    """
    PUBLIC
    an entry page for each list which displays additional (non-editable)
    information about the list such as the date of the last post and the
    time the last digest is sent.
    """
    error=None
    user_is_subscribed = False
    if request.method == 'POST':
        return redirect("list_summary", fqdn_listname=request.POST["list"])
    else:
        try:
            the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
            try:
                the_list.get_member(request.user.username)
                user_is_subscribed = True
            except:
                pass #init
        except MailmanApiError:
            return render_api_error(request)
    return render_to_response(template,
                              {'list':the_list,
                               'message':  None,
                               'user_is_subscribed':user_is_subscribed,
                              },
                              context_instance=RequestContext(request)
                              )
def list_summary(request, fqdn_listname, option=None ,template='mailmanweb/lists/summary.html'):
    """
    an entry page for each lists which allows some simple tasks per LIST
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except MailmanApiError:
        return utils.render_api_error(request)
    return render_to_response(template, 
        {'list': the_list,
         'subscribe_form': ListSubscribe(
            initial={'email':request.user.email}),},
        context_instance=RequestContext(request))

def list_subscribe(request, fqdn_listname):
    """Subscribe to a list.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
        if request.method == 'POST':
            form = ListSubscribe(request.POST)
            if form.is_valid():
                email = request.POST.get('email')
                real_name = request.POST.get('real_name')
                the_list.subscribe(email, real_name)
                messages.success(request,_('You are now subscribed to %s.' % the_list.fqdn_listname))
                return redirect('list_summary', the_list.fqdn_listname)
            else:
                logger.debug(form)
        else:
            form = ListSubscribe()
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request,e.msg)
        return redirect('list_summary', the_list.fqdn_listname)
    return render_to_response('mailmanweb/lists/subscribe.html', 
                              {'form': form, 'list': the_list,},
                              context_instance=RequestContext(request))

def list_unsubscribe(request, fqdn_listname, email):
    """Unsubscribe from a list.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except MailmanApiError:
        return utils.render_api_error(request)
    try:
        the_list.unsubscribe(email)
        messages.success(request, '%s has been unsubscribed from this list.' %
                         email)
    except ValueError, e:
        messages.error(request, e)
    return redirect('list_summary', the_list.fqdn_listname)

def list_subscriptions(request, option=None, fqdn_listname=None, user_email = None,
                       template = 'mailmanweb/lists/subscriptions.html', *args, **kwargs):#TODO **only kwargs ?
    """
    Display the information there is available for a list. This 
    function also enables subscribing or unsubscribing a user to a 
    list. For the latter two different forms are available for the 
    user to fill in which are evaluated in this function.
    """
    #create Values for Template usage   
    message = None
    error = None
    form_subscribe = None
    form_unsubscribe = None
    if request.POST.get('fqdn_listname', ''):
        fqdn_listname = request.POST.get('fqdn_listname', '')
    # connect REST and catch issues getting the list
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except AttributeError, e:
        return render_to_response('mailmanweb/errors/generic.html', 
                                  {'error': "REST API not found / Offline"},
                                  context_instance=RequestContext(request))
    #process submitted form    
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
                    response = the_list.subscribe(address=email,real_name=form.cleaned_data.get('real_name', ''))
                    return render_to_response('mailmanweb/lists/summary.html', 
                                              {'list': the_list,
                                               'option':option,
                                               'message':_("Subscribed ")+ email },context_instance=RequestContext(request))
                except HTTPError, e:
                    return render_to_response('mailmanweb/errors/generic.html', 
                                      {'error':e}, context_instance=RequestContext(request))
            else: #invalid subscribe form
                form_subscribe = form
                form_unsubscribe = ListUnsubscribe(initial = {'fqdn_listname': fqdn_listname, 'name' : 'unsubscribe'})       
        elif request.POST.get('name', '') == "unsubscribe":
            form = ListUnsubscribe(request.POST)
            if form.is_valid():
                #the form was valid so try to unsubscribe the user
                try:
                    email = form.cleaned_data["email"]
                    response = the_list.unsubscribe(address=email)
                    return render_to_response('mailmanweb/lists/summary.html', 
                                              {'list': the_list, 'message':_("Unsubscribed ")+ email },context_instance=RequestContext(request))
                except ValueError, e:
                    return render_to_response('mailmanweb/errors/generic.html', 
                                      {'error':e}, context_instance=RequestContext(request))   
            else:#invalid unsubscribe form
                form_subscribe = ListSubscribe(initial = {'fqdn_listname': fqdn_listname,
                                                               'option':option,
                                                               'name' : 'subscribe'})
                form_unsubscribe = ListUnsubscribe(request.POST)
    else:
        # the request was a GET request so set the two forms to empty
        # forms
        if option=="subscribe" or not option:
            form_subscribe = ListSubscribe(initial = {'fqdn_listname': fqdn_listname, 'email':request.user.username, 
                                             'name' : 'subscribe'})
        if option=="unsubscribe" or not option:                                             
            form_unsubscribe = ListUnsubscribe(initial = {'fqdn_listname': fqdn_listname, 'email':request.user.username, 
                                                 'name' : 'unsubscribe'})
    the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)#TODO
    return render_to_response(template, {'form_subscribe': form_subscribe,
                                         'form_unsubscribe': form_unsubscribe,
                                         'message':message,
                                         'error':error,
                                         'list': the_list,
                                         }
                                         ,context_instance=RequestContext(request))

@login_required
def list_delete(request, fqdn_listname):
    """Deletes a list but asks for confirmation first.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except MailmanApiError:
        return utils.render_api_error(request)
    if request.method == 'POST':
        the_list.delete()
        # let the user return to the list index page
        lists = List.objects.all()
        return redirect("list_index")
    else:
        submit_url = reverse('list_delete',kwargs={'fqdn_listname':fqdn_listname})
        cancel_url = reverse('list_index',)
        return render_to_response('mailmanweb/confirm_dialog.html',
                    {'submit_url': submit_url,
                     'cancel_url': cancel_url,
                    'list':the_list,},
                    context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser)
def list_held_messages(request, fqdn_listname):
    """Shows a list of held messages.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except MailmanApiError:
        return utils.render_api_error(request)
    return render_to_response('mailmanweb/lists/held_messages.html',
                {'list':the_list,},
                context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser)
def accept_held_message(request, fqdn_listname, msg_id):
    """Accepts a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
        the_list.accept_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request,e.msg)
        return redirect('list_held_messages', the_list.fqdn_listname)
    messages.successful(request, 'The message has been accepted.')
    return redirect('list_held_messages', the_list.fqdn_listname)

@user_passes_test(lambda u: u.is_superuser)
def discard_held_message(request, fqdn_listname, msg_id):
    """Accepts a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
        the_list.discard_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request,e.msg)
        return redirect('list_held_messages', the_list.fqdn_listname)
    messages.successful(request, 'The message has been discarded.')
    return redirect('list_held_messages', the_list.fqdn_listname)

@user_passes_test(lambda u: u.is_superuser)
def defer_held_message(request, fqdn_listname, msg_id):
    """Accepts a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
        the_list.defer_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request,e.msg)
        return redirect('list_held_messages', the_list.fqdn_listname)
    messages.successful(request, 'The message has been defered.')
    return redirect('list_held_messages', the_list.fqdn_listname)

@user_passes_test(lambda u: u.is_superuser)
def reject_held_message(request, fqdn_listname, msg_id):
    """Accepts a held message.
    """
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
        the_list.reject_message(msg_id)
    except MailmanApiError:
        return utils.render_api_error(request)
    except HTTPError, e:
        messages.error(request,e.msg)
        return redirect('list_held_messages', the_list.fqdn_listname)
    messages.successful(request, 'The message has been rejected.')
    return redirect('list_held_messages', the_list.fqdn_listname)

@login_required
def list_settings(request, fqdn_listname=None, visible_section=None, visible_option=None,
                  template='mailmanweb/lists/settings.html'):
    """
    View and edit the settings of a list.
    The function requires the user to be logged in and have the 
    permissions necessary to perform the action.
    
    Use /<NAMEOFTHESECTION>/<NAMEOFTHEOPTION>
    to show only parts of the settings
    <param> is optional / is used to differ in between section and option might result in using //option
    """
    message = ""
    logger.debug(visible_section)
    if visible_section == None:
        visible_section = 'List Identity'
    form_sections = []
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except MailmanApiError:
        return utils.render_api_error(request)
    #collect all Form sections for the links:
    temp = ListSettings('','')
    for section in temp.layout:
        try:
            form_sections.append((section[0],temp.section_descriptions[section[0]]))
        except KeyError, e:
            error=e
    del temp
    #Save a Form Processed by POST  
    if request.method == 'POST':
        form = ListSettings(visible_section,visible_option,data=request.POST)
        form.truncate()
        if form.is_valid():
            list_settings = the_list.settings
            for key in form.fields.keys():
                list_settings[key] = form.cleaned_data[key]
                list_settings.save()    
            message = _("The list has been updated.")
        else:
            message = _("Validation Error - The list has not been updated.")
    
    else:
        #Provide a form with existing values
        #create form and process layout into form.layout
        form = ListSettings(visible_section,visible_option,data=None)
        #create a Dict of all settings which are used in the form
        used_settings={}
        for section in form.layout:
            for option in section[1:]:
                used_settings[option] = the_list.settings[option]
        #recreate the form using the settings
        form = ListSettings(visible_section,visible_option,data=used_settings)
        form.truncate()
    return render_to_response(template, {'form': form,
                                         'form_sections': form_sections,
                                         'message': message,
                                         'list': the_list,
                                         'visible_option':visible_option,
                                         'visible_section':visible_section,
                                         }
                                         ,context_instance=RequestContext(request))

@login_required
def mass_subscribe(request, fqdn_listname=None, 
                   template='mailmanweb/lists/mass_subscribe.html'):
    """
    Mass subscribe users to a list.
    This functions is part of the settings for a list and requires the
    user to be logged in to perform the action.
    """
    message = ""
    try:
        the_list = List.objects.get_or_404(fqdn_listname=fqdn_listname)
    except MailmanApiError:
        return utils.render_api_error(request)
    if request.method == 'POST':
        form = ListMassSubscription(request.POST)
        if form.is_valid():
            try:
                # The emails to subscribe should each be provided on a
                # separate line so get each of them.
                emails = request.POST["emails"].splitlines()
                for email in emails:
                    # very simple test if email address is valid
                    parts = email.split('@')
                    if len(parts) == 2 and '.' in parts[1]: #TODO - move check to clean method of the form - see example in django docs
                        try:
                            the_list.subscribe(address=email, real_name="")
                            message = "The mass subscription was successful."
                        except Exception, e: #TODO find right exception and catch only this one
                            return render_to_response('mailmanweb/errors/generic.html', 
                                  {'error': str(e)})

                    else:
                        # At least one email address wasn't valid so 
                        # overwrite the success message and ask them to
                        # try again.
                        message = "Please enter valid email addresses."
            except Exception, e:
                return HttpResponse(e)
    else:
        # A request to view the page was send so return the form to
        # mass subscribe users.
        form = ListMassSubscription()
    return render_to_response(template, {'form': form,
                                         'message': message,
                                         'list': the_list}
                                         ,context_instance=RequestContext(request))

@login_required
def user_mailmansettings(request):
    try:
        the_user = MailmanUser.objects.get(address=request.user.email)
    except MailmanApiError:
        return utils.render_api_error(request)

    settingsform = MembershipSettings()
    return render_to_response('mailmanweb/user_mailmansettings.html',
                              {'mm_user': the_user, 
                               'settingsform': settingsform},
                              context_instance=RequestContext(request))
@login_required
def user_settings(request, tab = "membership",
                  template = 'mailmanweb/user_settings.html',
                  fqdn_listname = None,):
    """
    Change the user or the membership settings.
    The user must be logged in to be allowed to change any settings.
    TODO: * add CSS to display tabs ??
          * add missing functionality in REST server and client and 
            change to the correct calls here
    """
    member = request.user.username
    message = ''
    form = None
    the_list=None
    membership_lists = []

    try:
        c = Client('%s/3.0' % settings.REST_SERVER, settings.API_USER, settings.API_PASS)
        if tab == "membership":
            if fqdn_listname:
                the_list = List.objects.get(fqdn_listname=fqdn_listname)
                user_object = the_list.get_member(member)
            else:
                message = ("Using a workaround to replace missing Client functionality → LP:820827")
                for mlist in List.objects.all(): 
                    try: 
                        mlist.get_member(member)
                        membership_lists.append(mlist)
                    except:
                        pass
        else:
           # address_choices for the 'address' field must be a list of 
           # tuples of length 2
           raise Exception("WORK in PROGRRESS needs REST Auth Middleware! - TODO")
           address_choices = [[addr, addr] for addr in user_object.address]
    except AttributeError, e:
        return render_to_response('mailmanweb/errors/generic.html', 
                                  {'error': str(e)+"REST API not found / Offline"},
                                  context_instance=RequestContext(request))
    except ValueError, e:
        return render_to_response('mailmanweb/errors/generic.html', 
                                  {'error': e},
                                  context_instance=RequestContext(request))
    except HTTPError,e :
        return render_to_response('mailmanweb/errors/generic.html', 
                                  {'error': _("List ")+fqdn_listname+_(" does not exist")},
                                  context_instance=RequestContext(request))
    #-----------------------------------------------------------------
    if request.method == 'POST':
        # The form enables both user and member settings. As a result
        # we must find out which was the case.
        raise Exception("Please fix bug prior submitting the form")
        if tab == "membership":
            form = MembershipSettings(request.POST)
            if form.is_valid():
                member_object = c.get_member(member, request.GET["list"])
                member_object.update(request.POST)
                message = "The membership settings have been updated."
        else:
            # the post request came from the user tab
            # the 'address' field need choices as a tuple of length 2
            addr_choices = [[request.POST["address"], request.POST["address"]]]
            form = UserSettings(addr_choices, request.POST)
            if form.is_valid(): 
                user_object.update(request.POST)
                # to get the full list of addresses we need to 
                # reinstantiate the form with all the addresses
                # TODO: should return the correct settings from the DB,
                # not just the address_choices (add mock data to _User 
                # class and make the call with 'user_object.info')
                form = UserSettings(address_choices)
                message = "The user settings have been updated."

    else:
        if tab == "membership" and fqdn_listname :
            if fqdn_listname:
                #TODO : fix LP:821069 in mailman.client
                the_list = List.objects.get(fqdn_listname=fqdn_listname)
                member_object = the_list.get_member(member)
                # TODO: add delivery_mode and deliver_status from a 
                # list of tuples at one point, currently we hard code
                # them in forms.py
                # instantiate the form with the correct member info
                """
                acknowledge_posts
                hide_address
                receive_list_copy
                receive_own_postings
                delivery_mode
                delivery_status
                """
                data = {} #Todo https://bugs.launchpad.net/mailman/+bug/821438
                form = MembershipSettings(data)
        elif tab == "user":
            # TODO: should return the correct settings from the DB,
            # not just the address_choices (add mock data to _User 
            # class and make the call with 'user_object._info') The 'language'
            # field must also be added as a list of tuples with correct
            # values (is currently hard coded in forms.py).
            data ={}#Todo https://bugs.launchpad.net/mailman/+bug/821438
            form = UserSettings(data)

    return render_to_response(template, {'form': form,
                                         'tab': tab,
                                         'list': the_list,
                                         'membership_lists': membership_lists,
                                         'message': message,
                                         'member': member}
                                         ,context_instance=RequestContext(request))

def user_logout(request):
    logout(request)
    return redirect('user_login')

def user_login(request,template = 'mailmanweb/login.html'):
    if request.method == 'POST':
        form = AuthenticationForm(request.POST)
        user = authenticate(username=request.POST.get('username'),
                            password=request.POST.get('password'))
        if user is not None:
            logger.debug(user)
            if user.is_active:
                login(request,user)
                return redirect(request.GET.get('next', 'list_index'))
    else:
        form = AuthenticationForm()
    return render_to_response(template, {'form': form,},
                              context_instance=RequestContext(request))

def user_profile(request, user_email = None):
    if not request.user.is_authenticated():
        return redirect('user_login')
    #try:
    #    the_user = User.objects.get(email=user_email)
    #except MailmanApiError:
    #    return utils.render_api_error(request)
    return render_to_response('mailmanweb/user_profile.html',
    #                          {'mm_user': the_user},
                              context_instance=RequestContext(request))
    
def user_todos(request):
    return render_to_response('mailmanweb/user_todos.html',
                              context_instance=RequestContext(request))
    