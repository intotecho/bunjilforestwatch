//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

org.anotherearth.view.EquateHeadingsButtonStrategy = function() {}; //implements Observer update strategy
org.anotherearth.view.EquateHeadingsButtonStrategy.prototype = {
	execute: function(button) {
		//org.anotherearth.Interface.ensureImplements(button, org.anotherearth.GUIWidget);
		var props = button.getModel().getCurrentCameraProperties();
		(props.leftEarth.head === props.rightEarth.head) ? button.setIsEnabled(false) : button.setIsEnabled(true);
	}
};
