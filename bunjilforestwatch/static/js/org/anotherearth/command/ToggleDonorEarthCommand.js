//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.command = window.org.anotherearth.command || {};

org.anotherearth.command.ToggleDonorEarthCommand = function(earthsController) {
	var earthsController = earthsController;

	this.execute = function(option) {
		earthsController.toggleDonorEarth(option.value);
	};
};
