from django import forms
from django import template
from django.template.loader import render_to_string
from django.conf import settings

from umessages.models import MessageRecipient, MessageContact
import umessages
import re

register = template.Library()

class BaseMessageNode(template.Node):
    """
    Base helper class (abstract) for handling the get_message_* template tags.
    Looks a bit strange, but the subclasses below should make this a bit more
    obvious.

    """
    def render(self, context):
       qs = self.get_query_set(context)
       context[self.as_varname] = self.get_context_value_from_queryset(context, qs)
       return ''

    def get_query_set(self, context):
        """Subclasses should override this."""
        raise NotImplementedError

    def get_context_value_from_queryset(self, context, qs):
        """Subclasses should override this."""
        raise NotImplementedError


class MessageFormNode(BaseMessageNode):
    @classmethod
    def handle_token(cls, parser, token):
        """Class method to parse get_message_form and return a Node."""
        tokens = token.contents.split()

        # {% get_message_form as varname %}
        if len(tokens) == 3:
            if tokens[1] != 'as':
                raise template.TemplateSyntaxError("First argument in %r must be 'as'" % tokens[0])
            return cls(
                as_varname = tokens[2],
            )
            return cls()

        # {% get_message_form to to_user as varname %}
        if len(tokens) == 5:
            if tokens[1] != 'to':
                raise template.TemplateSyntaxError("First argument in %r tag must be 'to'" % tokens[0])
            if tokens[3] != 'as':
                raise template.TemplateSyntaxError("Third argument in %r must be 'as'" % tokens[0])
            return cls(
                to_user = tokens[2],
                as_varname = tokens[4]
            )
        else:
            raise template.TemplateSyntaxError("%r tag requires 2 or 4 arguments" % tokens[0])

    def __init__(self, to_user=None, as_varname=None):
        if to_user:
            self.to_user = template.Variable(to_user)
        else:
            self.to_user = to_user
        self.as_varname = as_varname

    """Insert a form for the message model into the context."""
    def get_form(self, context):
        form = umessages.get_form()()
        if self.to_user:
            try:
                user = self.to_user.resolve(context)
                form.fields['to'].initial = user
                form.fields['to'].widget = forms.HiddenInput()
            except template.VariableDoesNotExist:
                pass
        return form

    def render(self, context):
        context[self.as_varname] = self.get_form(context)
        return ''

    def get_query_set(self, context):
        return None

class RenderMessageFormNode(MessageFormNode):
    """Render the message form directly"""
    @classmethod
    def handle_token(cls, parser, token):
        """Class method to parse render_message_form and return a Node."""
        tokens = token.contents.split()

        # {% get_message_form %}
        if len(tokens) == 1:
            return cls()

        # {% get_message_form to to_user %}
        if len(tokens) == 3:
            if tokens[1] != 'to':
                raise template.TemplateSyntaxError("First argument in %r tag must be 'to'" % tokens[0])
            return cls(
                to_user = tokens[2],
            )

        raise template.TemplateSyntaxError("%r tag requires 0 or 2 arguments" % tokens[0])

    def render(self, context):
        template_search_list = [
            "umessages/_compose_form.html",
        ]
        context.push()
        formstr = render_to_string(template_search_list, {"form" : self.get_form(context)}, context)
        context.pop()
        return formstr

class MessageCount(template.Node):
    def __init__(self, from_user, var_name, to_user=None):
        self.user = template.Variable(from_user)
        self.var_name = var_name
        if to_user:
            self.to_user = template.Variable(to_user)
        else: self.to_user = to_user

    def render(self, context):
        try:
            user = self.user.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        if not self.to_user:
            message_count = MessageRecipient.objects.count_unread_messages_for(user)

        else:
            try:
                to_user = self.to_user.resolve(context)
            except template.VariableDoesNotExist:
                return ''

            message_count = MessageRecipient.objects.count_unread_messages_between(user,
                                                                                   to_user)

        context[self.var_name] = message_count

        return ''

@register.tag
def get_unread_message_count_for(parser, token):
    """
    Returns the unread message count for a user.

    Syntax::

        {% get_unread_message_count_for [user] as [var_name] %}

    Example usage::

        {% get_unread_message_count_for pero as message_count %}

    """
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name
    user, var_name = m.groups()
    return MessageCount(user, var_name)

@register.tag
def get_unread_message_count_between(parser, token):
    """
    Returns the unread message count between two users.

    Syntax::

        {% get_unread_message_count_between [user] and [user] as [var_name] %}

    Example usage::

        {% get_unread_message_count_between funky and wunki as message_count %}

    """
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) and (.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name
    from_user, to_user, var_name = m.groups()
    return MessageCount(from_user, var_name, to_user)

@register.tag
def get_message_form(parser, token):
    """
    Get a (new) form object to post a new message.

    Syntax::

        {% get_message_form as [varname] %}
        {% get_message_form to [user_object] as [varname] %}
    """
    return MessageFormNode.handle_token(parser, token)

@register.tag
def render_message_form(parser, token):
    """
    Render the message form (as returned by ``{% render_message_form %}``) through
    the ``umessages/_compose_form.html`` template.

    Syntax::

        {% render_message_form %}
        {% render_message_form to [user_object] %}
    """
    return RenderMessageFormNode.handle_token(parser, token)
