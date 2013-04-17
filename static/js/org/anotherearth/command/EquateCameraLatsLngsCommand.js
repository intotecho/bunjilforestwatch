//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.command = window.org.anotherearth.command || {};

//Panel 'class' - with reference to the Composite design pattern, a composite class

org.anotherearth.command.EquateCameraLatsLngsCommand = function(earthsController) { //implements Command interface
	var earthsController = earthsController;

	this.execute = function() {
		earthsController.equateCameraLatsLngs();
		earthsController.saveCameraProperties(false);
	};
};
