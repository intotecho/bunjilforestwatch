//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order


org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

org.anotherearth.view.EquateTiltsButtonStrategy = function() {}; //implements observer update stragegy
org.anotherearth.view.EquateTiltsButtonStrategy.prototype = {
	execute: function(button) {
		//org.anotherearth.Interface.ensureImplements(button, org.anotherearth.GUIWidget);
		var props = button.getModel().getCurrentCameraProperties();
		var leftTiltRounded = Math.round(props.leftEarth.tilt * 10)/10;  //Unlike other properties, tilt cannot apparently be
		var rightTiltRounded = Math.round(props.rightEarth.tilt * 10)/10;//set reliably with more than one decimal place of precision
		(leftTiltRounded === rightTiltRounded) ? button.setIsEnabled(false) : button.setIsEnabled(true);
	}
};
