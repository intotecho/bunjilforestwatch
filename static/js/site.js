/**
 * @name site.js
 * @version 1.0
 * @author Chris Goodman 
 * @fileoverview tools use throughout the site - loaded on every page.
 * e.g timeouts for the toaster messages.
 */


/**
 *  Delete enabled/disable 
 *  Used in entry.html to delete an entry
 *  @todo could reuse for deleting an area.
 */
$(function() {
	$("#sure").click(function() {
		if($(this).attr('checked') === 'checked')
		{
			$("#delete").removeClass('disabled');
			$("#delete").removeAttr('disabled');
		}
		else
		{
			$("#delete").addClass('disabled');
			$("#delete").attr('disabled', 'disabled');
		}
	});
});


// local functions

function filesizeformat(size)
{
	"use strict";
	if(size >= 1024 * 1024)
		return (size / (1024 * 1024)).toFixed(1) + ' MB';
	else
		return (size / 1024).toFixed(1) + ' KB';
}

// local commands
$(function() {
	"use strict";
	$('.dropdown-toggle').dropdown();
	$('.alert').alert();
	$('a[rel=tooltip], .show-tooltip').tooltip();
});


$(document).ready(function() {
	"use strict";
	$('[data-toggle=offcanvas]').click(function() {
	    $('.row-offcanvas').toggleClass('active');
	  });
	});

	var divs = document.getElementById("server-alerts").children;
	console.log('doc ready ' + divs);
	for(var i = 0; i < divs.length; i++){
		console.log(divs[i].innerHTML);
		addToasterMessage(divs[i].className, divs[i].innerHTML)
}

/**
 * Bootstrap Alert for ordinary page loads are handled by Jinja template base.html.
 * This is called when an ajax response requires an alert to pop up.
 * @param alert_p - one of 'alert-success', 'alert-info', 'alert-warning' or 'alert-danger'
 * @param message - to display
 * @example addToasterMessage('alert-success', 'ok message');
 */

function addToasterMessage(alert_p, message)
{
	"use strict";
	
	toastr.options = {
			  "closeButton": false,
			  "debug": false,
			  "newestOnTop": true,
			  "progressBar": false,
			  "positionClass": "toast-top-full-width",
			  "preventDuplicates": true,
			  "onclick": null,
			  "showDuration": "300",
			  "hideDuration": "1000",
			  "timeOut": "5000",
			  "extendedTimeOut": "60000",
			  "showEasing": "swing",
			  "hideEasing": "linear",
			  "showMethod": "fadeIn",
			  "hideMethod": "fadeOut"
			}
	toastr.info(message);
	
	var new_toast = $('#toast-message-template').clone();
	new_toast.prop('id', 'alert-id-' + Math.random());
	var alert_div = new_toast.find(".alert");
	var message_div = new_toast.find(".alert-message");
	//alert_div.html('<a class='close' href="#">' + message + ' &times;</a>');
	message_div.html(message);
	
	alert_div.addClass(alert_p);
	
	if (alert_p !== 'alert-danger') {
		alert_div.addClass('alert-dismissible');
		window.setTimeout(function() {
			alert_div.fadeTo(1500, 0).slideUp(1500, function(){
		        alert_div.remove(); 
		    });
		}, 15000);

	}
	
	//var position = $('#toaster-container').position();
	//console.log(position);
	//$("#toaster").css({left: position.left});

	new_toast.appendTo('#toaster').show();
			
	$('#toaster').stop().animate({
		  scrollTop: $("#toaster")[0].scrollHeight
		}, 800);
}

//fadeout and slide up bootstrap .alert messages after 10 seconds.
window.setTimeout(function() {
	"use strict";
    $(".alert-success").fadeTo(1500, 0).slideUp(1500, function(){
        $(this).remove(); 
    });
}, 15000);

window.setTimeout(function() {
	"use strict";
    $(".alert-info").fadeTo(1500, 0).slideUp(1500, function(){
        $(this).remove(); 
    });
}, 15000);

window.setTimeout(function() {
	"use strict";
    $(".alert-warning").fadeTo(1500, 0).slideUp(1500, function(){
        $(this).remove(); 
    });
}, 15000);



// don't fade out alert-error or alert-danger.

