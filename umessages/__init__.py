"""
Django messaging made easy.

"""
from django.conf import settings
from django.core import urlresolvers
from django.core.exceptions import ImproperlyConfigured
from umessages.forms import ComposeForm

from django.utils.importlib import import_module

VERSION = (1, 0, 0)

__version__ = '.'.join((str(each) for each in VERSION[:4]))

DEFAULT_MESSAGES_APP = 'umessages'

def get_version():
    """
    Returns string with digit parts only as version.

    """
    return '.'.join((str(each) for each in VERSION[:3]))

def get_message_app():
    """
    Get the message app (i.e. "umessages") as defined in the settings
    """
    # Make sure the app's in INSTALLED_APPS
    messages_app = get_message_app_name()
    if messages_app not in settings.INSTALLED_APPS:
        raise ImproperlyConfigured("The MESSAGES_APP (%r) "\
                                   "must be in INSTALLED_APPS" % settings.MESSAGES_APP)

    # Try to import the package
    try:
        package = import_module(messages_app)
    except ImportError as e:
        raise ImproperlyConfigured("The MESSAGES_APP setting refers to "\
                                   "a non-existing package. (%s)" % e)

    return package

def get_message_app_name():
    """
    Returns the name of the message app (either the setting value, if it
    exists, or the default).
    """
    return getattr(settings, 'MESSAGES_APP', DEFAULT_MESSAGES_APP)


def get_form():
    """
    Returns the message ModelForm class.
    """
    if get_message_app_name() != DEFAULT_MESSAGES_APP and hasattr(get_message_app(), "get_form"):
        return get_message_app().get_form()
    else:
        return MessageForm
