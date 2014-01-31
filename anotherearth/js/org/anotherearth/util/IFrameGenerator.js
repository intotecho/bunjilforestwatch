//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.util = window.org.anotherearth.util || {};

org.anotherearth.util.IFrameGenerator = {};
org.anotherearth.util.IFrameGenerator.createFrame = function() {
	var iframe = document.createElement('iframe');
	iframe.setAttribute('allowtransparency', 'false');
	iframe.scrolling = 'no';
	iframe.frameBorder = '0';
	iframe.src = (navigator.userAgent.indexOf('MSIE 6') >= 0) ? '' : 'javascript:void(0);';
	iframe.style.position = 'absolute';
	iframe.style.opacity = 0;
	iframe.style.top = 0;
	iframe.style.left = 0;
	iframe.style.width = '100%';
	iframe.style.height = '100%';
	iframe.style.zIndex = -1;
		
	return iframe;
};
