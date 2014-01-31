//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

org.anotherearth.view.EquateAltitudesButtonStrategy = function() {}; //implements Observer update stragegy
org.anotherearth.view.EquateAltitudesButtonStrategy.prototype = {
	execute: function(button) {
		//org.anotherearth.Interface.ensureImplements(button, org.anotherearth.GUIWidget);
		var props = button.getModel().getCurrentCameraProperties();
		(props.leftEarth.alt === props.rightEarth.alt) ? button.setIsEnabled(false) : button.setIsEnabled(true);
	}
};
