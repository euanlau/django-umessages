(function($)
{
    var scrollElement = 'html, body';
    var active_input = '';

    // Settings
    var MESSAGE_SCROLL_TOP_OFFSET = 40;

    var DEBUG = false

    $.fn.ready(function()
    {
        var messageform = $('form.js-messages-form');
        if ( messageform.length > 0 )
        {
            // Detect last active input.
            // Submit if return is hit, or any button other then preview is hit.
            messageform.find(':input').focus(setActiveInput).mousedown(setActiveInput);
            messageform.submit(onMessageFormSubmit);
        }

        var productMessageLink = $('.product-details-container .message-action-link');
        if (productMessageLink.length > 0)
        {
            productMessageLink.click(onMessageLinkClicked);
        }

        // Find the element to use for scrolling.
        // This code is much shorter then jQuery.scrollTo()
        $('html, body').each(function()
        {
            // See which tag updates the scrollTop attribute
            var $rootEl = $(this);
            var initScrollTop = $rootEl.attr('scrollTop');
            $rootEl.attr('scrollTop', initScrollTop + 1);
            if( $rootEl.attr('scrollTop') == initScrollTop + 1 )
            {
                scrollElement = this.nodeName.toLowerCase();
                $rootEl.attr('scrollTop', initScrollTop);  // Firefox 2 reset
                return false;
            }
        });


        // On load, scroll to proper message.
        var hash = window.location.hash;
        if( hash.substring(0, 2) == "#m" )
        {
            var id = parseInt(hash.substring(2));
            if( ! isNaN(id))   // e.g. #messages in URL
                scrollToMessage(id, 1000);
        }
    });


    function setActiveInput()
    {
        active_input = this.name;
    }


    function onMessageFormSubmit(event)
    {
        event.preventDefault();  // only after ajax call worked.
        var form = event.target;

        ajaxMessage(form, {
            onsuccess: onMessagePosted,
        });
        return false;
    }

    function onMessageLinkClicked(event)
    {
        event.preventDefault();  // only after ajax call worked.
        var link = event.target;
        $('.product-details-container #compose-message-form').toggle('slow');

        return false;
    }


    function scrollToMessage(id, speed)
    {
        // Allow initialisation before scrolling.
        var $message = $("#m" + id);
        if( $message.length == 0 ) {
            if( window.console ) console.warn("scrollToMessage() - #m" + id + " not found.");
            return;
        }

        if( window.on_scroll_to_message && window.on_scroll_to_message({message: $message}) === false )
            return;

        // Scroll to the message.
        scrollToElement( $message, speed, MESSAGE_SCROLL_TOP_OFFSET );
    }


    function scrollToElement( $element, speed, offset )
    {
        if( $element.length )
            $(scrollElement).animate( {scrollTop: $element.offset().top - (offset || 0) }, speed || 1000 );
    }


    function onMessagePosted( message_id, $message )
    {
        setTimeout(function(){ scrollToMessage(message_id, 1000); }, 1000);
    }


    /*
      Based on django-ajaxmessages, BSD licensed.
      Copyright (c) 2009 Brandon Konkle and individual contributors.

      Updated to be more generic, more fancy, and usable with different templates.
     */
    var messageBusy = false;

    function ajaxMessage(form, args)
    {
        var onsuccess = args.onsuccess;

        $('li.message-error').remove();
        if (messageBusy) {
            return false;
        }

        messageBusy = true;
        var $form = $(form);
        var message = $form.serialize();
        var url = $form.attr('action') || './';
        var ajaxurl = $form.attr('data-ajax-action');

        // Add a wait animation
        $('#message-waiting').fadeIn(1000);

        // Use AJAX to post the message.
        $.ajax({
            type: 'POST',
            url: ajaxurl || url,
            data: message,
            dataType: 'json',
            success: function(data) {
                messageBusy = false;
                removeWaitAnimation();
                removeErrors();

                if (data.success) {
                    var $added;

                    $added = messageSuccess(data);

                    if( onsuccess )
                        args.onsuccess(data.message_id, $added);
                }
                else {
                    messageFailure(data);
                }
            },
            error: function(data) {
                messageBusy = false;
                removeWaitAnimation();

                // Submit as non-ajax instead
                //$form.unbind('submit').submit();
            }
        });

        return false;
    }

    function messageSuccess(data)
    {
        // Clean form
        $('form.js-messages-form textarea').last().val("");
        $('#id_message').val('');

        // Show message
        var $messages = getMessagesDiv();
        if ($messages.length > 0 ) {
            $messages.append(data['html']).removeClass('empty');
            var $new_message = $messages.children("li.message-item:last");

            // Smooth introduction to the new message.
            $new_message.hide().show(600);
        }
        else {
            $('form.js-messages-form').fadeOut('slow').slideUp('slow');
            $('.product-details-container .product-message-success').show('slow');
        }
        return $new_message;
    }

    function messageFailure(data)
    {
        // Show mew errors
        for (var field_name in data.errors) {
            if(field_name) {
                var $field = $('#id_' + field_name);

                // Twitter bootstrap style
                $field.after('<span class="js-errors">' + data.errors[field_name] + '</span>');
                $field.closest('.control-group').addClass('error');
            }
        }
    }

    function removeErrors()
    {
        $('form.js-messages-form .js-errors').remove();
        $('form.js-messages-form .control-group.error').removeClass('error');
    }

    function getMessagesDiv()
    {
        var $messages = $("ul.message-list");
        if( $messages.length == 0 ) {
            if (DEBUG)
                alert("Internal error - unable to display message.\n\nreason: container is missing in the page.");
        }
        else {
        }
        return $messages;
    }

    function removeWaitAnimation()
    {
        // Remove the wait animation and message
        $('#message-waiting').hide().stop();
    }

})(window.jQuery);
