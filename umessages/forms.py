from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from umessages.fields import CommaSeparatedUserField
from umessages.models import Message, MessageRecipient

class ComposeForm(forms.Form):
    to = CommaSeparatedUserField(label=_("To"))
    body = forms.CharField(label=_("Message"),
                           widget=forms.Textarea({
                               'class': 'message',
                               'placeholder': _('Write a new message...')
                           }),
                           required=True)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'compose-message-form'
        self.helper.form_class = 'form-horizontal js-messages-form'
        self.helper.form_method = 'post'
        self.helper.form_action =  reverse('umessages-compose')
        self.helper.attrs = {
            'data-ajax-action' : reverse('umessages-compose-ajax')
        }
        self.helper.add_input( Submit('submit', _('Send'), css_class='pull-right') )

        super(ComposeForm, self).__init__(*args, **kwargs)

    def save(self, sender):
        """
        Save the message and send it out into the wide world.

        :param sender:
            The :class:`User` that sends the message.

        :param parent_msg:
            The :class:`Message` that preceded this message in the thread.

        :return: The saved :class:`Message`.

        """
        to_user_list = self.cleaned_data['to']
        body = self.cleaned_data['body']

        msg = Message.objects.send_message(sender,
                                           to_user_list,
                                           body)

        return msg
