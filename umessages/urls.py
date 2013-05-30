from django.conf.urls.defaults import *
from umessages import views as messages_views
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('',
    url(r'^compose/$',
        messages_views.MessageComposeFormView.as_view(),
        name='umessages_compose'),

    url(r'^compose/ajax/$', messages_views.MessageComposeAjaxFormView.as_view(),
        name='umessages-compose-ajax'),

    url(r'^compose/(?P<recipients>[\+\.\w]+)/$',
        messages_views.MessageComposeFormView.as_view(),
        name='umessages_compose_to'),



    url(r'^view/(?P<username>[\.\w]+)/$',
        login_required(messages_views.MessageDetailListView.as_view()),
        name='umessages_detail'),

    url(r'^remove/$',
        messages_views.message_remove,
        name='umessages_remove'),

    url(r'^unremove/$',
        messages_views.message_remove,
        {'undo': True},
        name='umessages_unremove'),

    url(r'^$',
        login_required(messages_views.MessageListView.as_view()),
        name='umessages_list'),
)
