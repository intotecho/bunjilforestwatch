// speech support
$(function() {
	if(document.createElement('input').webkitSpeech != undefined)
	{
		$(".post-speech").before('\
						<div class="form-group"> \
							<label class="control-label" for="speech">speech</label> \
							<div class="controls"> \
								<input class="input-lg" rows=10 id="speech" name="speech" type="text" x-webkit-speech /> \
								<span class="help-inline">click the mic icon and your speech will be added below</span> \
							</div> \
						</div> \
		');

		$("#speech").bind('webkitspeechchange', function() {
			text = $("#text");
			speech = $("#speech").val() + ".";
			$("#speech").val('');
			speech = speech.substr(0, 1).toUpperCase() + speech.substr(1);
			if(text.val() != "")
				text.val(text.val() + " " + speech);
			else
				text.val(speech);
		});
	}
});

// delete enabled/disable
$(function() {
	$("#sure").click(function() {
		if($(this).attr('checked') == 'checked')
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
	if(size >= 1024 * 1024)
		return (size / (1024 * 1024)).toFixed(1) + ' MB';
	else
		return (size / 1024).toFixed(1) + ' KB';
}

// local commands

$(function() {
	$('.dropdown-toggle').dropdown();
	$('.alert').alert();
	$('a[rel=tooltip], .show-tooltip').tooltip();
});


$(document).ready(function() {
	$('[data-toggle=offcanvas]').click(function() {
	    $('.row-offcanvas').toggleClass('active');
	  });
	});

//fadeout and slide up bootstrap .alert messages after 10 seconds.
window.setTimeout(function() {
    $(".alert-info").fadeTo(1500, 0).slideUp(1500, function(){
        $(this).remove(); 
    });
}, 15000);

window.setTimeout(function() {
    $(".alert-warning").fadeTo(1500, 0).slideUp(1500, function(){
        $(this).remove(); 
    });
}, 15000);

window.setTimeout(function() {
    $(".alert-error").fadeTo(1500, 0).slideUp(1500, function(){
        $(this).remove(); 
    });
}, 15000);

window.setTimeout(function() {
    $(".alert-success").fadeTo(1500, 0).slideUp(1500, function(){
        $(this).remove(); 
    });
}, 15000);
// don't fade out alert-error or alert-danger.

