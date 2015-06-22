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

from django.conf.urls import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import login as login_view

from postorius.views import *
from postorius.views.generic import *


per_list_urlpatterns = patterns('postorius.views',
                                url(r'^members/(?P<page>\d+)/$',
                                    ListMembersView.as_view(
                                    ), name='list_members_paged'),
                                url(r'^csv_view/$',
                                    'csv_view', name='csv_view'),
                                url(r'^members/$',
                                    ListMembersView.as_view(
                                    ), name='list_members'),
                                url(r'^members/options/(?P<email>[^/]+)/$',
                                    ListMemberOptionsView.as_view(
                                    ), name='list_member_options'),
                                url(r'^metrics$',
                                    ListMetricsView.as_view(
                                    ), name='list_metrics'),
                                url(r'^$',
                                    ListSummaryView.as_view(
                                    ), name='list_summary'),
                                url(r'^subscribe$',
                                    ListSubscribeView.as_view(
                                    ), name='list_subscribe'),
                                url(r'^change_subscription$',
                                    ChangeSubscriptionView.as_view(),
                                    name='change_subscription'),
                                url(r'^unsubscribe/(?P<email>[^/]+)$',
                                    ListUnsubscribeView.as_view(
                                    ), name='list_unsubscribe'),
                                url(r'^subscriptions$',
                                    'list_subscriptions',
                                    name='list_subscriptions'),
                                url(r'^subscription_requests$',
                                    'list_subscription_requests',
                                    name='list_subscription_requests'),
                                url(r'^handle_subscription_request/(?P<request_id>[^/]+)/(?P<action>[accept|reject|discard|defer]+)$',
                                    'handle_subscription_request',
                                    name='handle_subscription_request'),
                                url(r'^mass_subscribe/$',
                                    ListMassSubscribeView.as_view(
                                    ), name='mass_subscribe'),
                                url(r'^mass_removal/$',
                                    ListMassRemovalView.as_view(
                                    ), name='mass_removal'),
                                url(r'^delete$',
                                    'list_delete', name='list_delete'),
                                url(r'^held_messages/(?P<msg_id>[^/]+)/'
                                    'accept$', 'accept_held_message',
                                    name='accept_held_message'),
                                url(r'^held_messages/(?P<msg_id>[^/]+)/'
                                    'discard$', 'discard_held_message',
                                    name='discard_held_message'),
                                url(r'^held_messages/(?P<msg_id>[^/]+)/'
                                    'defer$', 'defer_held_message',
                                    name='defer_held_message'),
                                url(r'^held_messages/(?P<msg_id>[^/]+)/'
                                    'reject$', 'reject_held_message',
                                    name='reject_held_message'),
                                url(r'^held_messages$',
                                    'list_held_messages',
                                    name='list_held_messages'),
                                url(r'^remove/(?P<role>[^/]+)/'
                                    '(?P<address>[^/]+)',
                                    'remove_role', name='remove_role'),
                                url(r'^settings/(?P<visible_section>[^/]+)?$',
                                    'list_settings',
                                    name='list_settings'),
                                url(r'^unsubscribe_all$',
                                    'remove_all_subscribers', name='unsubscribe_all'),
                                url(r'^archival_options$',
                                    'list_archival_options',
                                    name='list_archival_options'),
                                )

urlpatterns = patterns(
    'postorius.views',
    (r'^$', 'list_index'),
    # /account/
    url(r'^accounts/login/$', login_view,
        {"template_name": "postorius/login.html"}, name='user_login'),
    url(r'^accounts/logout/$', 'user_logout', name='user_logout'),
    url(r'^accounts/profile/$', 'user_profile', name='user_profile'),
    url(r'^accounts/subscriptions/$', UserSubscriptionsView.as_view(),
        name='user_subscriptions'),
    url(r'^accounts/per-address-preferences/$',
        UserAddressPreferencesView.as_view(), name='user_address_preferences'),
    url(r'^accounts/per-subscription-preferences/$',
        UserSubscriptionPreferencesView.as_view(
        ), name='user_subscription_preferences'),
    url(r'^accounts/mailmansettings/$',
        UserMailmanSettingsView.as_view(),
        name='user_mailmansettings'),
    #/dashboard/
    url(r'^user_dashboard/$',
        AdminTasksView.as_view(),
        name='user_dashboard'),
    url(r'^user_dashboard/(?P<list_id>[^/]+)/(?P<msg_id>[\d+]+)/(?P<action>[accept|reject|discard|defer]+)$',
        'handle_mod_task',
        name='handle_mod_task'),
    url(r'^user_dashboard/(?P<list_id>[^/]+)/(?P<sub_id>[^/]+)/(?P<action>[accept|reject|discard]+)$',
        'handle_sub_task',
        name='handle_sub_task'),
    url(r'^user_dashboard/(?P<task_id>[^/]+)/(?P<priority>[^/]+)$',
        'set_task_priority',
        name='set_task_priority'),
    url(r'^user_dashboard/(?P<reorder_param>[\w+]+)$',
        'reorder_tasks_by',
        name='reorder_tasks_by'),
    url(r'^user_dashboard/(?P<list_id>[^/]+)/(?P<role>[^/]+)/(?P<email>[^/]+)$',
        'remove_role_tasks',
        name='remove_role_tasks'),
    url(r'^user_dashboard/(?P<task_id>[^/]+)$',
        'discard_manual_task',
        name='discard_manual_task'),
    
    # /settings/
    url(r'^settings/$', 'site_settings', name="site_settings"),
    url(r'^domains/$', 'domain_index', name='domain_index'),
    url(r'^domains/new/$', 'domain_new', name='domain_new'),
    url(r'^domains/(?P<domain>[^/]+)/delete$',
        'domain_delete', name='domain_delete'),
    # /lists/
    url(r'^lists/$', 'list_index', name='list_index'),
    url(r'^lists/new/$', 'list_new', name='list_new'),
    url(r'^lists/(?P<list_id>[^/]+)/', include(per_list_urlpatterns)),
    url(r'^users/address_activation/$',
        AddressActivationView.as_view(),
        name='address_activation'),
    url(r'^users/address_activation/(?P<activation_key>[A-Za-z0-9]{40})/$',
        'address_activation_link', name='address_activation_link'),
)
