//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};

$(document).ready(function() {org.anotherearth.init();});

org.anotherearth.init = function() {
	delete org.anotherearth.init;
	$('#' + org.anotherearth.JS_INCOMPATIBILITY_MESSAGE_ID).remove();//removes JavaScript incompatibility message

	if (!google.earth.isSupported()) {
		var mapsIncompatibleMessageContainer = document.createElement('div');
		$(mapsIncompatibleMessageContainer).addClass("ui-state-highlight").addClass("panel").addClass("ui-widget");
		var mapsIncompatibleMessage = document.createElement('p');
		mapsIncompatibleMessageContainer.id = org.anotherearth.PLUGIN_INCOMPATIBILITY_MESSAGE_ID;
		mapsIncompatibleMessageContainer.appendChild(mapsIncompatibleMessage);
		$('body').append(mapsIncompatibleMessageContainer);
		var incompatiblityMessageText = "Sorry; the combination of browser and operating system you are using is incompatible " +
			                              "with the Google Earth plugin upon which this application relies.";
		mapsIncompatibleMessage.appendChild(document.createTextNode(incompatiblityMessageText));
		mapsIncompatibleMessageContainer.id = org.anotherearth.PLUGIN_INCOMPATIBILITY_MESSAGE_ID;
		mapsIncompatibleMessageContainer.appendChild(mapsIncompatibleMessage);
		$('body').append(mapsIncompatibleMessageContainer);
		org.anotherearth.util.Translator.translatePage();
	} 
	else {
		$('#' + org.anotherearth.PLAIN_HTML_MESSAGE_ID).remove();//removes plain HTML welcome message
		var container = org.anotherearth.Container.getInstance();//instantiates objects, creating invisible GUI elements

		//quirk workarounds
		if (navigator.userAgent.indexOf('Firefox/2') > 0) {
			$('#' + org.anotherearth.CP_ID).css('width', '18em');//FF2 fills available space with div if no width is given
			$('.ui-dropdownchecklist').addClass('FF2_checklist');
		}

		$('#' + org.anotherearth.CP_ID).css('position', 'absolute');//chrome (and webkit?) for some reason assigns position:relative to this element

		if(!$.support.leadingWhitespace) {//if is IE
			$('.panel').css('padding-bottom', '1em').css('left', '240px');//truncates them for some reason and since immobile, cannot be blocking search boxes
			$('#' + org.anotherearth.CP_ID).css('width', '18em').css('left', '240px');//IE fills available space with div if no width is given
			$('.drag_handle').remove();
		}

		if (typeof document.body.style.maxHeight === "undefined") {//if IE6
			$('.ui-dropdownchecklist-dropcontainer').css('width', '10em');
			$('.ui-dropdownchecklist-text').css('width', '10em');
			$('.ui-dropdownchecklist-item').css('width', '10em');
			$('span.ui-dropdownchecklist-text').text("");
			$('.ui-dropdownchecklist-dropcontainer input:first-child').attr('checked', false);
		}

		//create earths and canvases
		var leftEarth  = container.getComponent('leftEarth');
		var rightEarth = container.getComponent('rightEarth');
	
		//FIXME why is this here?
		var _canvasResizer = function() {
			var viewportWidth = $(window).width(); 
			var viewportHeight = window.innerHeight ? window.innerHeight : $(window).height(); //height finding complicated by Opera 9 workaround
			leftEarth.setCanvasPositionAndSize(0, 0, viewportWidth/2-30, viewportHeight-40);
			rightEarth.setCanvasPositionAndSize(0, viewportWidth/2-10, viewportWidth/2-30, viewportHeight-40);
		};
		
		$(window).resize(_canvasResizer);//dynamic canvas resizing
		_canvasResizer();
		
		container.getComponent('welcomePanel').show();
		leftEarth.createEarthInstance();
		rightEarth.createEarthInstance();
		org.anotherearth.util.Translator.translatePage();
	}
};
