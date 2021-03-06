from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.views.generic.list import ListView
from django.views.generic.edit import FormView
from django.template.loader import render_to_string
from django.template import RequestContext

from braces.views import AjaxResponseMixin
from braces.views import JSONResponseMixin

from umessages import signals
from umessages.models import Message, MessageRecipient, MessageContact
from umessages.forms import ComposeForm
from umessages.utils import get_datetime_now, get_user_model
from umessages import appsettings as umessages_settings

class MessageListView(ListView):
    """

    Returns the message list for this user. This is a list contacts
    which at the top has the user that the last conversation was with. This is
    an imitation of the iPhone SMS functionality.

    """
    page=1
    paginate_by=50
    template_name='umessages/message_list.html'
    extra_context={}
    context_object_name = 'message_list'

    def get_context_data(self, **kwargs):
        context = super(MessageListView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    def get_queryset(self):
        return MessageContact.objects.get_contacts_for(self.request.user)

class MessageDetailListView(MessageListView):
    """

    Returns a conversation between two users

    """
    paginate_by=10

    template_name='umessages/message_detail.html'

    def get_context_data(self, **kwargs):
        context = super(MessageDetailListView, self).get_context_data(**kwargs)
        context['recipient'] = self.recipient
        return context

    def get_queryset(self):
        username = self.kwargs['username']
        self.recipient = get_object_or_404(get_user_model(),
                                  username__iexact=username)
        queryset = Message.objects.get_conversation_between(self.request.user,
                                                        self.recipient)
        self._update_unread_messages(queryset)
        return queryset

    def _update_unread_messages(self, queryset):
        message_pks = [m.pk for m in queryset]
        unread_list = MessageRecipient.objects.filter(message__in=message_pks,
                                                  user=self.request.user,
                                                  read_at__isnull=True)
        now = get_datetime_now()
        unread_list.update(read_at=now)


class MessageDetailAjaxListView(JSONResponseMixin, AjaxResponseMixin, MessageDetailListView):
    http_method_names = ['get',]
    new_element_template_name = 'umessages/_message_detail_list.html'
    def get_ajax(self, request, *args, **kwargs):
        action = self.request.method
        success = True
        last = False

        self.object_list = self.get_queryset()
        context = self.get_context_data(object_list=self.object_list)

        last = not context['page_obj'].has_next()

        html = render_to_string(self.new_element_template_name,
                                context,
                                context_instance=RequestContext(request))

        json_dict = {
            'success': success,
            'action': action,
            'html' : html,
            'last' : last,
        }

        return self.render_json_response(json_dict)

class MessageComposeFormView(FormView):
    """
    Compose a new message

    :recipients:
        String containing the usernames to whom the message is send to. Can be
        multiple username by seperating them with a ``+`` sign.

    :param compose_form:
        The form that is used for getting neccesary information. Defaults to
        :class:`ComposeForm`.

    :param success_url:
        String containing the named url which to redirect to after successfull
        sending a message. Defaults to `umessages-list`` if there are
        multiple recipients. If there is only one recipient, will redirect to
        `umessages-detail`` page, showing the conversation.

    :param template_name:
        String containing the name of the template that is used.

    :param recipient_filter:
        A list of :class:`User` that don"t want to receive any messages.

    :param extra_context:
        Dictionary with extra variables supplied to the template.

    **Context**

    ``form``
        The form that is used.

    """
    template_name = "umessages/message_form.html"
    success_url = None
    form_class = ComposeForm
    recipients = None
    recipient_filter = None
    extra_context = {}
    http_method_names = ['get', 'post', 'put']

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(MessageComposeFormView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super(MessageComposeFormView, self).get_initial()
        if self.recipients:
            username_list = [r.strip() for r in self.recipients.split("+")]
            recipients = [u for u in get_user_model().objects.filter(username__in=username_list)]
            initial["to"] = recipients
        return initial

    def get_success_url(self):
        requested_redirect = self.request.REQUEST.get(REDIRECT_FIELD_NAME,
                                                      False)
        redirect_to = reverse('umessages-list')
        if requested_redirect:
            redirect_to = requested_redirect
        elif self.success_url:
            redirect_to = self.success_url
        elif len(self.recipients) == 1:
            redirect_to = reverse('umessages-detail',
                                  kwargs={'username': self.recipients[0].username})

        print redirect_to
        return redirect_to

    def form_valid(self, form):
        self.message = form.save(self.request.user)
        signals.message_sent.send(
            sender=self.message.__class__ ,
            message=self.message,
            request=self.request)

        self.recipients = self.message.recipients.all()

        if umessages_settings.UMESSAGES_USE_MESSAGES:
            messages.success(self.request, _('Message is sent.'),
                             fail_silently=True)
        return super(MessageComposeFormView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(MessageComposeFormView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

class MessageComposeAjaxFormView(JSONResponseMixin, AjaxResponseMixin, MessageComposeFormView):
    http_method_names = ['post',]
    new_element_template_name = 'umessages/_message.html'
    def post_ajax(self, request, *args, **kwargs):
        data = request.POST.copy()
        action = self.request.method
        success = True
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        json_errors = {}
        if form.errors:
            for field_name in form.errors:
                field = form[field_name]
                json_errors[field_name] = _render_errors(field)
            success = False

        json_dict = {
            'success': success,
            'action': action,
            'errors': json_errors,
        }

        message = form.save(self.request.user)
        signals.message_sent.send(
            sender=message.__class__,
            message=message,
            request=self.request
        )

        if message is not None:
            context = {
                'message' : message,
                'action' : action
            }

            message_html = render_to_string('umessages/_message.html',
                                            context,
                                            context_instance=RequestContext(request))

            json_dict.update({
                'html': message_html,
                'message_id':message.id
            })

        return self.render_json_response(json_dict)

@login_required
@require_http_methods(["POST"])
def message_remove(request, undo=False):
    """
    A ``POST`` to remove messages.

    :param undo:
        A Boolean that if ``True`` unremoves messages.

    POST can have the following keys:

        ``message_pks``
            List of message id's that should be deleted.

        ``next``
            String containing the URI which to redirect to after the keys are
            removed. Redirect defaults to the inbox view.

    The ``next`` value can also be supplied in the URI with ``?next=<value>``.

    """
    message_pks = request.POST.getlist('message_pks')
    redirect_to = request.REQUEST.get(REDIRECT_FIELD_NAME, False)

    if message_pks:
        # Check that all values are integers.
        valid_message_pk_list = set()
        for pk in message_pks:
            try: valid_pk = int(pk)
            except (TypeError, ValueError): pass
            else:
                valid_message_pk_list.add(valid_pk)

        # Delete all the messages, if they belong to the user.
        now = get_datetime_now()
        changed_message_list = set()
        for pk in valid_message_pk_list:
            message = get_object_or_404(Message, pk=pk)

            # Check if the user is the owner
            if message.sender == request.user:
                if undo:
                    message.sender_deleted_at = None
                else:
                    message.sender_deleted_at = now
                message.save()
                changed_message_list.add(message.pk)

            # Check if the user is a recipient of the message
            if request.user in message.recipients.all():
                mr = message.messagerecipient_set.get(user=request.user,
                                                      message=message)
                if undo:
                    mr.deleted_at = None
                else:
                    mr.deleted_at = now
                mr.save()
                changed_message_list.add(message.pk)

        # Send messages
        if (len(changed_message_list) > 0) and umessages_settings.UMESSAGES_USE_MESSAGES:
            if undo:
                message = ungettext('Message is succesfully restored.',
                                    'Messages are succesfully restored.',
                                    len(changed_message_list))
            else:
                message = ungettext('Message is successfully removed.',
                                    'Messages are successfully removed.',
                                    len(changed_message_list))

            messages.success(request, message, fail_silently=True)

    if redirect_to: return redirect(redirect_to)
    else: return redirect(reverse('umessages-list'))
