
org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

org.anotherearth.view.EquateLatLngsButtonStrategy = function() {}; //implements Observer update stragegy
org.anotherearth.view.EquateLatLngsButtonStrategy.prototype = {
	execute: function(button) {
		//org.anotherearth.Interface.ensureImplements(button, org.anotherearth.GUIWidget);
		var props = button.getModel().getCurrentCameraProperties();
		if (props.leftEarth.lat    === props.rightEarth.lat &&
		    props.leftEarth.lng === props.rightEarth.lng) {
			button.setIsEnabled(false);
		}
		else {	
			button.setIsEnabled(true);
		}
	}
};
