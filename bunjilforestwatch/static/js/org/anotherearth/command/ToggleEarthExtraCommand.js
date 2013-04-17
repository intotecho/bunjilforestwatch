//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.command = window.org.anotherearth.command || {};

org.anotherearth.command.ToggleEarthExtraCommand = function(earthsController) {
	var earthsController;

	this.execute = function(selectBox, option) {
		var earthId = ((selectBox.id === org.anotherearth.CP_R_EARTH_EXTRAS_SELECTOR_ID) ? 'REarth' : 'LEarth'); 
		earthsController.toggleEarthExtra(earthId, option.value);
	};
};
