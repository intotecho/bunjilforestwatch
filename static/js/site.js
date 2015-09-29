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

//fadeout and slide up bootstrap .alert messages after 10 seconds.
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

window.setTimeout(function() {
	"use strict";
    $(".alert-error").fadeTo(1500, 0).slideUp(1500, function(){
        $(this).remove(); 
    });
}, 15000);

window.setTimeout(function() {
	"use strict";
    $(".alert-success").fadeTo(1500, 0).slideUp(1500, function(){
        $(this).remove(); 
    });
}, 15000);
// don't fade out alert-error or alert-danger.

