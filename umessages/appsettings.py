# Umessages settings file.
#
# Please consult the docs for more information about each setting.

from django.conf import settings
gettext = lambda s: s

CRISPY_TEMPLATE_PACK = getattr(settings, 'CRISPY_TEMPLATE_PACK', 'bootstrap')

"""
Boolean value that defines ifumessages should use the django messages
framework to notify the user of any changes.
"""
UMESSAGES_USE_MESSAGES = getattr(settings,
                                 'UMESSAGES_USE_MESSAGES',
                                 True)
