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

	$('#admin-test-1').click(admin_test_1);
	$('#admin-test-2').click(admin_test_2);
	$('#admin-test-3').click(admin_test_3);
	$('#admin-test-4').click(admin_test_4);
	
	var divs = document.getElementById("server-alerts").children;
	//console.log('doc ready ' + divs);
	for(var i = 0; i < divs.length; i++){
		console.log(divs[i].innerHTML);
		addToasterMessage(divs[i].className, divs[i].innerHTML);
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
			  "positionClass": "toast-top-center",
			  "preventDuplicates": false,
			  "onclick": null,
			  "showDuration": "300",
			  "hideDuration": "1000",
			  "timeOut": "5000",
			  "extendedTimeOut": "6000",
			  "showEasing": "swing",
			  "hideEasing": "linear",
			  "showMethod": "fadeIn",
			  "hideMethod": "fadeOut"
			}
	switch(alert_p) {
	case 'alert-success':
		toastr.success(message);
		break;

	case 'alert-info':
		toastr.info(message);
		break;

	case 'alert-warning':
		toastr.warning(message);
		break;

	case 'alert-danger':
		toastr.options.closeButton = true;
		toastr.options.timeOut = "15000";
		toastr.options.extendedTimeOut =  "10000";

		toastr.error(message);
		break;
	}
	
}

function admin_test_1()
{
	console.log('admin test 1');
	toastr.success('Success message');
}

function admin_test_2()
{
	console.log('admin test 2');
	toastr.info('Info message');
}
function admin_test_3()
{
	console.log('admin test 3');
	toastr.warning ('Warning message - a long message lorem ipsum facto bro axis');
}
function admin_test_4()
{
	console.log('admin test 4');
	toastr.error('Error message');
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

/**
 * From: http://stackoverflow.com/questions/5717093/check-if-a-javascript-string-is-an-url
 * @return true is string is a valid URL
 */
function isURL(str) {
	  var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
	  '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.?)+[a-z]{2,}|'+ // domain name
	  '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
	  '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
	  '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
	  '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
	  return pattern.test(str);
	}

// don't fade out alert-error or alert-danger.

