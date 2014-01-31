//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.command = window.org.anotherearth.command || {};

org.anotherearth.command.UndoCommand = function(earthsController) { //implements Command
	var earthsController = earthsController;
	var enabled = true;

	this.execute = function() {
		if (!enabled) {//race-condition bug prevention
			return;
		}
		enabled = false;
		earthsController.undo();
		enabled = true;
	};
};
