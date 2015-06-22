# -*- coding: utf-8 -*-
# Copyright (C) 2012-2015 by the Free Software Foundation, Inc.
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

from django import forms
from django.core.validators import validate_email, URLValidator
from django.utils.translation import ugettext_lazy as _
from fieldset_forms import FieldsetForm


class DomainNew(FieldsetForm):

    """
    Form field to add a new domain
    """
    mail_host = forms.CharField(
        label=_('Mail Host'),
        error_messages={'required': _('Please a domain name'),
                        'invalid': _('Please enter a valid domain name.')},
        required=True)
    web_host = forms.CharField(
        label=_('Web Host'),
        error_messages={'required': _('Please a domain name'),
                        'invalid': _('Please enter a valid domain name.')},
        required=True)
    description = forms.CharField(
        label=_('Description'),
        required=False)

    def clean_mail_host(self):
        mail_host = self.cleaned_data['mail_host']
        try:
            validate_email('mail@' + mail_host)
        except:
            raise forms.ValidationError(_("Please enter a valid domain name"))
        return mail_host

    def clean_web_host(self):
        web_host = self.cleaned_data['web_host']
        try:
            URLValidator()(web_host)
        except:
            raise forms.ValidationError(_("Please enter a valid domain name"))
        return web_host

    class Meta:

        """
        Class to handle the automatic insertion of fieldsets and divs.

        To use it: add a list for each wished fieldset. The first item in
        the list should be the wished name of the fieldset, the following
        the fields that should be included in the fieldset.
        """
        layout = [["Please enter Details",
                   "mail_host",
                   "web_host",
                   "description"]]


class NewOwnerForm(forms.Form):

    """Add a list owner."""
    owner_email = forms.EmailField(
        label=_('Email Address'),
        error_messages={
            'required': _('Please enter an email adddress.'),
            'invalid': _('Please enter a valid email adddress.')})


class NewModeratorForm(forms.Form):

    """Add a list moderator."""
    moderator_email = forms.EmailField(
        label=_('Email Address'),
        error_messages={
            'required': _('Please enter an email adddress.'),
            'invalid': _('Please enter a valid email adddress.')})

class TaskSearchForm(forms.Form):

    """Search For Tasks on Dashboard."""
    search_tasks = forms.CharField(
        label=_('Search Tasks'),
        required=True,
        widget=forms.TextInput(attrs={'class': "form-control", 'placeholder' : "Filter Tasks"}),
        error_messages={
            'required': _('Search Field Can\'t be empty'),
            'invalid': _('Search Query Not valid')})

class ListIndexSearchForm(forms.Form):

    """Search among List Index for a List on Dashboard."""
    search_li = forms.CharField(
        label=_('Search Lists'),
        required=True,
        widget=forms.TextInput(attrs={'class': "form-control", 'placeholder' : "Search"}),
        error_messages={
            'required': _('Search Field Can\'t be empty'),
            'invalid': _('Invalid List Search query')})

class NewManualTaskForm(forms.Form):

    """Form instance to add a Manual Task To Dashboard."""
    mtask_subject = forms.CharField(
        label=_('Subject Description for Manual Task'),
        required=True,
        widget=forms.TextInput(),
        error_messages={
            'required': _('Task Heading can\'t e empty'),
            'invalid': _('Invalid Set of Characters')})
    mtask_description = forms.CharField(
        label=_('Full Description for The User Manual Task'),
        required=True,
        widget=forms.TextInput(),
        error_messages={
            'invalid': _('Invalid Set of Characters')})
		    
class GlobalSearchForm(forms.Form):

    """Global Search for Entities on Dashboard."""
    query_field = forms.CharField(
        label=_('Dashboard Global Search Query'),
        required=True,
        widget=forms.TextInput(),
        error_messages={
            'required': _('Search Query Can\'t be None'),
            'invalid': _('Invalid Query')})
   
    check_lists = forms.BooleanField(
        required=False,
        label=_('Search Among Lists'),
            )
    check_domains = forms.BooleanField(
        required=False,
        label=_('Search Among Domains'),
            )
    check_people = forms.BooleanField(
        required=False,
        label=_('Search Among People'),
            )

class ListNew(FieldsetForm):

    """
    Form fields to add a new list. Languages are hard coded which should
    be replaced by a REST lookup of available languages.
    """
    listname = forms.CharField(
        label=_('List Name'),
        required=True,
        error_messages={'required': _('Please enter a name for your list.'),
                        'invalid': _('Please enter a valid list name.')})
    mail_host = forms.ChoiceField()
    list_owner = forms.EmailField(
        label=_('Inital list owner address'),
        error_messages={
            'required': _("Please enter the list owner's email address.")},
        required=True)
    advertised = forms.ChoiceField(
        widget=forms.RadioSelect(),
        label=_('Advertise this list?'),
        error_messages={
            'required': _("Please choose a list type.")},
        required=True,
        choices=(
            (True, _("Advertise this list in list index")),
            (False, _("Hide this list in list index"))))
    description = forms.CharField(
        label=_('Description'),
        required=True)

    def __init__(self, domain_choices, *args, **kwargs):
        super(ListNew, self).__init__(*args, **kwargs)
        self.fields["mail_host"] = forms.ChoiceField(
            widget=forms.Select(),
            label=_('Mail Host'),
            required=True,
            choices=domain_choices,
            error_messages={'required': _("Choose an existing Domain."),
                            'invalid': "ERROR-todo_forms.py"})
        if len(domain_choices) < 2:
            self.fields["mail_host"].help_text = _(
                "Site admin has not created any domains")
            # if len(choices) < 2:
            #    help_text=_("No domains available: " +
            #                "The site admin must create new domains " +
            #                "before you will be able to create a list")

    def clean_listname(self):
        try:
            validate_email(self.cleaned_data['listname'] + '@example.net')
        except:
            raise forms.ValidationError(_("Please enter a valid listname"))
        return self.cleaned_data['listname']

    class Meta:

        """
        Class to handle the automatic insertion of fieldsets and divs.

        To use it: add a list for each wished fieldset. The first item in
        the list should be the wished name of the fieldset, the following
        the fields that should be included in the fieldset.
        """
        layout = [["List Details",
                   "listname",
                   "mail_host",
                   "list_owner",
                   "description",
                   "advertised"], ]


class ListSubscribe(FieldsetForm):
    """Form fields to join an existing list.
    """

    email = forms.ChoiceField(label=_('Your email address'),
                validators=[validate_email],
                widget=forms.Select(),
                error_messages={'required': _('Please enter an email address.'),
                                'invalid': _('Please enter a valid email address.')})

    display_name = forms.CharField(label=_('Your name (optional)'),
                                   required=False)

    def __init__(self, user_emails, *args, **kwargs):
        super(ListSubscribe, self).__init__(*args, **kwargs)
        self.fields['email'].choices = ((address, address)
                                        for address in user_emails)


class ListUnsubscribe(FieldsetForm):

    """Form fields to leave an existing list.
    """
    email = forms.EmailField(
        label=_('Your email address'),
        widget=forms.HiddenInput(),
        error_messages={
            'required': _('Please enter an email address.'),
            'invalid': _('Please enter a valid email address.')})


class ArchivePolicySettingsForm(forms.Form):
    """
    Set the general archive policy.
    """
    archive_policy_choices = (
        ("public", _("Public Archives")),
        ("private", _("Private Archives")),
        ("never", _("Do not archive this list")),
    )
    archive_policy = forms.ChoiceField(
        choices=archive_policy_choices,
        widget=forms.RadioSelect,
        label=_('Archive Policy'),
        help_text=_('Policy for archiving messages for this list'),
    )


class MessageAcceptanceForm(forms.Form):
    """
    List messages acceptance settings.
    """
    action_choices = (
        ("hold", _("Hold for moderator")),
        ("reject", _("Reject (with notification)")),
        ("discard", _("Discard (no notification)")),
        ("accept", _("Accept")),
        ("defer", _("Defer")))
    acceptable_aliases = forms.CharField(
        widget=forms.Textarea(),
        label=_("Acceptable aliases"),
        required=False,
        help_text=(
            'Alias names which qualify as explicit to or cc destination names '
            'for this list. Alternate addresses that are acceptable when '
            '`require_explicit_destination\' is enabled. This option takes a '
            'list of regular expressions, one per line, which is matched '
            'against every recipient address in the message. The matching is '
            'performed with Python\'s re.match() function, meaning they are '
            'anchored to the start of the string.'))
    administrivia = forms.BooleanField(
        widget=forms.RadioSelect(choices=((True, _('Yes')), (False, _('No')))),
        required=False,
        label=_('Administrivia'),
        help_text=(
            'Administrivia tests will check postings to see whether it\'s '
            'really meant as an administrative request (like subscribe, '
            'unsubscribe, etc), and will add it to the the administrative '
            'requests queue, notifying the administrator of the new request, '
            'in the process.'))
    default_member_action = forms.ChoiceField(
        widget=forms.RadioSelect(),
        label=_('Default action to take when a member posts to the list:'),
        error_messages={
            'required': _("Please choose a default member action.")},
        required=True,
        choices=action_choices,
        help_text=(
            'Default action to take when a member posts to the list. '
            'Hold -- This holds the message for approval by the list '
            'moderators.'
            'Reject -- this automatically rejects the message by sending a '
            'bounce notice to the post\'s author. The text of the bounce '
            'notice can be configured by you. '
            'Discard -- this simply discards the message, with no notice '
            'sent to the post\'s author. '
            'Accept --accepts any postings to the list by default. '
            'Defer -- Defers any postings to the list by default. '))
    default_nonmember_action = forms.ChoiceField(
        widget=forms.RadioSelect(),
        label=_('Default action to take when a non-member posts to the'
                'list:'),
        error_messages={
            'required': _("Please choose a default non-member action.")},
        required=True,
        choices=action_choices,
        help_text=(
            'When a post from a non-member is received, the message\'s sender '
            'is matched against the list of explicitly accepted, held, '
            'rejected (bounced), and discarded addresses. '
            'If no match is found, then this action is taken.'))


class DigestSettingsForm(forms.Form):
    """
    List digest settings.
    """
    digest_size_threshold = forms.DecimalField(
        label=_('Digest size threshold'),
        help_text=('How big in Kb should a digest be before it gets sent '
                   'out?'))


class AlterMessagesForm(forms.Form):
    """
    Alter messages list settings.
    """
    filter_content = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((True, _('Yes')), (False, _('No'))),
        widget=forms.RadioSelect,
        required=False,
        label=_('Filter content'),
        help_text=(
            'Should Mailman filter the content of list traffic according to '
            'the settings below?'))
    collapse_alternatives = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((True, _('Yes')), (False, _('No'))),
        widget=forms.RadioSelect,
        required=False,
        label=_('Collapse alternatives'),
        help_text=(
            'Should Mailman collapse multipart/alternative to its first part '
            'content?'))
    convert_html_to_plaintext = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((True, _('Yes')), (False, _('No'))),
        widget=forms.RadioSelect,
        required=False,
        label=_('Convert html to plaintext'),
        help_text=(
            'Should Mailman convert text/html parts to plain text? This '
            'conversion happens after MIME attachments have been stripped.'))
    anonymous_list = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((True, _('Yes')), (False, _('No'))),
        widget=forms.RadioSelect,
        required=False,
        label=_('Anonymous list'),
        help_text=(
            'Hide the sender of a message, replacing it with the list address '
            '(Removes From, Sender and Reply-To fields)'))
    include_rfc2369_headers = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((True, _('Yes')), (False, _('No'))),
        widget=forms.RadioSelect,
        required=False,
        label= _('Include RFC2369 headers'),
        help_text=_(
            'Yes is highly recommended. RFC 2369 defines a set of List-* '
            'headers that are normally added to every message sent to the '
            'list membership. These greatly aid end-users who are using '
            'standards compliant mail readers. They should normally always '
            'be enabled. However, not all mail readers are standards '
            'compliant yet, and if you have a large number of members who are '
            'using non-compliant mail readers, they may be annoyed at these '
            'headers. You should first try to educate your members as to why '
            'these headers exist, and how to hide them in their mail clients. '
            'As a last resort you can disable these headers, but this is not '
            'recommended (and in fact, your ability to disable these headers '
            'may eventually go away).'))
    allow_list_posts = forms.TypedChoiceField(
        choices=((True, _('Yes')), (False, _('No'))),
        widget=forms.RadioSelect,
        label=_("Include the list post header"),
        help_text=_(
            "This can be set to no for announce lists that do not wish to "
            "include the List-Post header because posting to the list is "
            "discouraged."))
    reply_to_address = forms.CharField(
        label=_('Explicit reply-to address'),
        required=False,
        help_text=_(
            'This option allows admins to set an explicit Reply-to address. '
            'It is only used if the reply-to is set to use an explicitly set '
            'header'))
    first_strip_reply_to = forms.TypedChoiceField(
        coerce=lambda x: x == 'False',
        choices=((True, _('Yes')), (False, _('No'))),
        widget=forms.RadioSelect,
        required=False,
        help_text=_(
            'Should any existing Reply-To: header found in the original '
            'message be stripped? If so, this will be done regardless of '
            'whether an explict Reply-To: header is added by Mailman or not.'))
    reply_goes_to_list = forms.ChoiceField(
        label=_('Reply goes to list'),
        widget=forms.Select(),
        required=False,
        error_messages={
            'required': _("Please choose a reply-to action.")},
        choices=(
            ("no_munging", _("No Munging")),
            ("point_to_list", _("Reply goes to list")),
            ("explicit_header", _("Explicit Reply-to header set"))),
        help_text=(
            'Where are replies to list messages directed? No Munging is '
            'strongly recommended for most mailing lists. \nThis option '
            'controls what Mailman does to the Reply-To: header in messages '
            'flowing through this mailing list. When set to No Munging, no '
            'Reply-To: header is '
            'added by Mailman, although if one is present in the original '
            'message, it is not stripped. Setting this value to either Reply '
            'to List or Explicit Reply causes Mailman to insert a specific '
            'Reply-To: header in all messages, overriding the header in the '
            'original message if necessary (Explicit Reply inserts the value '
            'of reply_to_address). There are many reasons not to introduce or '
            'override the Reply-To: header. One is that some posters depend '
            'on their own Reply-To: settings to convey their valid return '
            'address. Another is that modifying Reply-To: makes it much more '
            'difficult to send private replies. See `Reply-To\' Munging '
            'Considered Harmful for a general discussion of this issue. '
            'See Reply-To Munging Considered Useful for a dissenting opinion. '
            'Some mailing lists have restricted '
            'posting privileges, with a parallel list devoted to discussions. '
            'Examples are `patches\' or `checkin\' lists, where software '
            'changes are posted by a revision control system, but discussion '
            'about the changes occurs on a developers mailing list. To '
            'support these types of mailing lists, select Explicit Reply and '
            'set the Reply-To: address option to point to the parallel list.'))
    posting_pipeline = forms.ChoiceField(
        label=_('Pipeline'),
        widget=forms.Select(),
        required=False,
        error_messages={
            'required': _("Please choose a reply-to action.")},
        choices=(
            ("default-owner-pipeline", _("default-owner-pipeline")),
            ("default-posting-pipeline", _("default-posting-pipeline")),
            ("virgin", _("virgin"))),
        help_text=(
            'Type of pipeline you want to use for this mailing list'))


class ListAutomaticResponsesForm(forms.Form):
    """
    List settings for automatic responses.
    """
    autorespond_choices = (
        ("respond_and_continue", _("Respond and continue processing")),
        ("respond_and_discard", _("Respond and discard message")),
        ("none", _("No automatic response")))
    autorespond_owner = forms.ChoiceField(
        choices=autorespond_choices,
        widget=forms.RadioSelect,
        label=_('Autorespond to list owner'),
        help_text=(
            'Should Mailman send an auto-response to emails sent to the '
            '-owner address?'))
    autoresponse_owner_text = forms.CharField(
        label=_('Autoresponse owner text'),
        widget=forms.Textarea(),
        required=False,
        help_text=('Auto-response text to send to -owner emails.'))
    autorespond_postings = forms.ChoiceField(
        choices=autorespond_choices,
        widget=forms.RadioSelect,
        label=_('Autorespond postings'),
        help_text=(
            'Should Mailman send an auto-response to mailing list posters?'))
    autoresponse_postings_text = forms.CharField(
        label=_('Autoresponse postings text'),
        widget=forms.Textarea(),
        required=False,
        help_text=('Auto-response text to send to mailing list posters.'))
    autorespond_requests = forms.ChoiceField(
        choices=autorespond_choices,
        widget=forms.RadioSelect,
        label=_('Autorespond requests'),
        help_text=(
            'Should Mailman send an auto-response to emails sent to the '
            '-request address? If you choose yes, decide whether you want '
            'Mailman to discard the original email, or forward it on to the '
            'system as a normal mail command.'))
    autoresponse_request_text = forms.CharField(
        label=_('Autoresponse request text'),
        widget=forms.Textarea(),
        required=False,
        help_text=('Auto-response text to send to -request emails.'))
    autoresponse_grace_period = forms.CharField(
        label=_('Autoresponse grace period'),
        help_text=(
            'Number of days between auto-responses to either the mailing list '
            'or -request/-owner address from the same poster. Set to zero '
            '(or negative) for no grace period (i.e. auto-respond to every '
            'message).'))
    send_welcome_message = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((True, _('Yes')), (False, _('No'))),
        widget=forms.RadioSelect,
        required=False,
        label=_('Send welcome message'),
        help_text=(
            'Send welcome message to newly subscribed members? '
            'Turn this off only if you plan on subscribing people manually '
            'and don\'t want them to know that you did so. This option is '
            'most useful for transparently migrating lists from some other '
            'mailing list manager to Mailman.'))
    welcome_message_uri = forms.CharField(
        label=_('URI for the welcome message'),
        help_text=_(
            'If a welcome message is to be sent to subscribers, you can '
            'specify a URI that gives the text of this message.'),
    )
    admin_immed_notify = forms.BooleanField(
        widget=forms.RadioSelect(choices=((True, _('Yes')), (False, _('No')))),
        required=False,
        label=_('Admin immed notify'),
        help_text=(
            'Should the list moderators get immediate notice of new requests, '
            'as well as daily notices about collected ones? List moderators '
            '(and list administrators) are sent daily reminders of requests '
            'pending approval, like subscriptions to a moderated list, '
            'or postings that are being held for one reason or another. '
            'Setting this option causes notices to be sent immediately on the '
            'arrival of new requests as well. '))
    admin_notify_mchanges = forms.BooleanField(
        widget=forms.RadioSelect(choices=((True, _('Yes')), (False, _('No')))),
        required=False,
        label=_('Notify admin of membership changes'),
        help_text=(
            'Should administrator get notices of subscribes and unsubscribes?'
            ))


class ListIdentityForm(forms.Form):
    """
    List identity settings.
    """
    advertised = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((True, _('Yes')), (False, _('No'))),
        widget=forms.RadioSelect,
        label=_('Show list on index page'),
        help_text=(
            'Choose whether to include this list on the list of all lists'))
    description = forms.CharField(
        label=_('Description'),
        help_text=(
            'This description is used when the mailing list is listed with '
            'other mailing lists, or in headers, and so forth. It should be '
            'as succinct as you can get it, while still identifying what the '
            'list is.'),
        widget=forms.Textarea())
    mail_host = forms.CharField(
        label=_('Mail Host'),
        error_messages={'required': _('Please a domain name'),
                        'invalid': _('Please enter a valid domain name.')},
        required=True,
        help_text=(
            "The \"host_name\" is the preferred name for email to "
            "'mailman-related addresses on this host, and generally should be "
            "the mail host's exchanger address, if any. This setting can be "
            "useful for selecting among alternative names of a host that "
            "has multiple addresses."))
    display_name = forms.CharField(
        label=_('Display name'),
        help_text=('Display name is the name shown in the web interface.')
    )
    subject_prefix = forms.CharField(
        label=_('Subject prefix'),
    )


SUBSCRIPTION_POLICY_CHOICES = (
    ('', _('Please Choose')),
    ('open', _('Open')),
    ('confirm', _('Confirm')),
    ('moderate', _('Moderate')),
    ('confirm_then_moderate', _('Confirm, then moderate')),
)


class ListSubscriptionPolicyForm(forms.Form):
    """
    List subscription policy settings.
    """    
    subscription_policy = forms.ChoiceField(
        label=_('Subscription Policy'),
        choices=SUBSCRIPTION_POLICY_CHOICES,
        help_text=_('Set the subscription policy.'))


class ListArchiverForm(forms.Form):
    """
    Select archivers for a list.
    """
    archivers = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label=_('Activate archivers for this list'))

    def __init__(self, archivers, *args, **kwargs):
        super(ListArchiverForm, self).__init__(*args, **kwargs)
        self.fields['archivers'].choices = sorted(
            [(key, key) for key in archivers.keys()])


class Login(FieldsetForm):

    """Form fields to let the user log in.
    """
    user = forms.EmailField(
        label=_('Email address'),
        error_messages={'required': _('Please enter an email address.'),
                        'invalid': _('Please enter a valid email address.')},
        required=True)
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput,
        error_messages={'required': _('Please enter your password.'),
                        'invalid': _('Please enter a valid password.')},
        required=True)

    class Meta:

        """
        Class to define the name of the fieldsets and what should be
        included in each.
        """
        layout = [["Login", "user", "password"]]


class ListMassSubscription(FieldsetForm):
    """Form fields to masssubscribe users to a list.
    """
    emails = forms.CharField(
        label=_('Emails to mass subscribe'),
        widget=forms.Textarea,
    )


class ListMassRemoval(FieldsetForm):

    """Form fields to remove multiple list users.
    """
    emails = forms.CharField(
        label=_('Emails to Unsubscribe'),
        widget=forms.Textarea,
    )

    class Meta:

        """
        Class to define the name of the fieldsets and what should be
        included in each.
        """
        layout = [["Mass Removal", "emails"]]


class UserPreferences(FieldsetForm):

    """
    Form handling the user's global, address and subscription based preferences
    """
    choices = ((True, _('Yes')), (False, _('No')))

    delivery_mode_choices = (("regular", _('Regular')),
                             ("plaintext_digests", _('Plain Text Digests')),
                             ("mime_digests", _('Mime Digests')),
                             ("summary_digests", _('Summary Digests')))
    delivery_status_choices = (
        ("enabled", _('Enabled')), ("by_user", _('Disabled')))
    delivery_status = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=delivery_status_choices,
        required=False,
        label=_('Delivery status'),
        help_text=_(
            'Set this option to Enabled to receive messages posted to this '
            'mailing list. Set it to Disabled if you want to stay subscribed, '
            'but don\'t want mail delivered to you for a while (e.g. you\'re '
            'going on vacation). If you disable mail delivery, don\'t forget '
            'to re-enable it when you come back; it will not be automatically '
            're-enabled.'))
    delivery_mode = forms.ChoiceField(
        widget=forms.Select(),
        choices=delivery_mode_choices,
        required=False,
        label=_('Delivery mode'),
        help_text=_(
            'If you select summary digests , you\'ll get posts bundled '
            'together (usually one per day but possibly more on busy lists), '
            'instead of singly when they\'re sent. Your mail reader may or '
            'may not support MIME digests. In general MIME digests are '
            'preferred, but if you have a problem reading them, select '
            'plain text digests.'))
    receive_own_postings = forms.BooleanField(
        widget=forms.RadioSelect(choices=choices),
        required=False,
        label=_('Receive own postings'),
        help_text=_(
            'Ordinarily, you will get a copy of every message you post to the '
            'list. If you don\'t want to receive this copy, set this option '
            'to No.'
            ))
    acknowledge_posts = forms.BooleanField(
        widget=forms.RadioSelect(choices=choices),
        required=False,
        label=_('Acknowledge posts'),
        help_text=_(
            'Receive acknowledgement mail when you send mail to the list?'))
    hide_address = forms.BooleanField(
        widget=forms.RadioSelect(choices=choices),
        required=False,
        label=_('Hide address'),
        help_text=_(
            'When someone views the list membership, your email address is '
            'normally shown (in an obscured fashion to thwart spam '
            'harvesters). '
            'If you do not want your email address to show up on this '
            'membership roster at all, select Yes for this option.'))
    receive_list_copy = forms.BooleanField(
        widget=forms.RadioSelect(choices=choices),
        required=False,
        label=_('Receive list copy'),
        help_text=_(
            'When you are listed explicitly in the To: or Cc: headers of a '
            'list message, you can opt to not receive another copy from the '
            'mailing list. Select Yes to avoid receiving copies from the '
            'mailing list; select No to receive copies. '))

    class Meta:

        """
        Class to define the name of the fieldsets and what should be
        included in each.
        """
        layout = [["User Preferences", "acknowledge_posts", "hide_address",
                   "receive_list_copy", "receive_own_postings",
                   "delivery_mode", "delivery_status"]]


class UserNew(FieldsetForm):

    """
    Form field to add a new user
    """
    display_name = forms.CharField(
        label=_('User Name'),
        required=True,
        error_messages={'required': _('Please enter a display name.'),
                        'invalid': _('Please enter a valid display name.')})
    email = forms.EmailField(
        label=_("User's email address"),
        error_messages={
            'required': _("Please enter the user's email address.")},
        required=True)
    password = forms.CharField(
        label=_('Password'),
        required=True,
        error_messages={'required': _('Please enter a password.')},
        widget=forms.PasswordInput(render_value=False))
    password_repeat = forms.CharField(
        label=_('Repeat password'),
        required=True,
        error_messages={'required': _('Please repeat the password.')},
        widget=forms.PasswordInput(render_value=False))

    def clean(self):
        cleaned_data = self.cleaned_data
        password = cleaned_data.get("password")
        password_repeat = cleaned_data.get("password_repeat")
        if password != password_repeat:
            raise forms.ValidationError("Passwords must be identical.")

        return cleaned_data


class UserSettings(FieldsetForm):

    """Form handling the user settings.
    """

    def __init__(self, address_choices, *args, **kwargs):
        """
        Initialize the user settings with a field 'address' where
        the values are set dynamically in the view.
        """
        super(UserSettings, self).__init__(*args, **kwargs)
        self.fields['address'] = forms.ChoiceField(
            choices=(address_choices),
            widget=forms.Select(),
            error_messages={'required': _("Please choose an address.")},
            required=True,
            label=_('Default email address'))

    id = forms.IntegerField(
        label=_('ID'),
        initial=9,
        widget=forms.HiddenInput(),
        required=False,
        error_messages={
            'invalid': _('Please provide an integer ID.')})
    mailing_list = forms.CharField(
        label=_('Mailing list'),
        widget=forms.HiddenInput(),
        required=False)
    display_name = forms.CharField(
        label=_('Display name'),
        required=False)
    preferred_language = forms.ChoiceField(
        label=_('Default/Preferred language'),
        widget=forms.Select(),
        error_messages={
            'required': _("Please choose a language.")},
        required=False,
        choices=(
            ("", _("Please choose")),
            ("English (USA)", "English (USA)")))
    password = forms.CharField(
        label=_('Change password'),
        widget=forms.PasswordInput,
        required=False,
        error_messages={'required': _('Please enter your password.'),
                        'invalid': _('Please enter a valid password.')})
    conf_password = forms.CharField(
        label=_('Confirm password'),
        widget=forms.PasswordInput,
        required=False,
        error_messages={'required': _('Please enter your password.'),
                        'invalid': _('Please enter a valid password.')})

    class Meta:

        """
        Class to define the name of the fieldsets and what should be
        included in each.
        """
        layout = [["User settings", "display_name", "password",
                   "conf_password", "preferred_language", "address"]]


class ListDeleteForm(forms.Form):
    list_name = forms.EmailField(widget=forms.HiddenInput())


class AddressActivationForm(forms.Form):
    email = forms.EmailField()
    user_email = forms.EmailField(widget=forms.HiddenInput)

    def clean(self):
        cleaned_data = super(AddressActivationForm, self).clean()
        email = cleaned_data.get('email')
        user_email = cleaned_data.get('user_email')
        if email == user_email:
            raise forms.ValidationError(_('Please provide a different email '
                                          'address than your own.'))
        return cleaned_data

class ChangeSubscriptionForm(forms.Form):
    email = forms.ChoiceField()

    def __init__(self, user_emails, *args, **kwargs):
        super(ChangeSubscriptionForm, self).__init__(*args, **kwargs)
        self.fields['email'] = forms.ChoiceField(
            label=_('Select Email'),
            required=False,
            widget=forms.Select(),
            choices=((address, address) for address in user_emails))
