//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.command = window.org.anotherearth.command || {};

org.anotherearth.command.EquateCameraTiltsCommand = function(earthsController) { //implements Command interface
	var earthsController = earthsController;

	this.execute = function() {
		earthsController.equateCameraTilts();
		earthsController.saveCameraProperties(false);
	};
};
