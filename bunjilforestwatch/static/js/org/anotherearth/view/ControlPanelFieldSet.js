//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order
/* not currently in use

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

org.anotherearth.view.ControlPanelFieldSet = function(fieldSetLegend, fieldSetId) {
	//private variables
	var fieldset;
	var fieldSetLegend = fieldSetLegend;
	var fieldSetId = fieldSetId;
	var controlPanelObjects = new org.anotherearth.util.ArrayList();

	//privileged methods
	this.createGUIElements = function() {
		fieldset = document.createElement('fieldset');
		
		if (fieldSetLegend.length !== 0) {
			var legend = document.createElement('legend');
			var legendText = document.createTextNode(fieldSetLegend);
			legend.appendChild(legendText);
			fieldset.appendChild(legend);
			$(fieldset).addClass('panel_fieldset');
		}
		else {
			$(fieldset).addClass('legendless_panel_fieldset');
		}
		fieldset.id = fieldSetId;
		fieldset.style.display = 'none';
	};
	this.addChild = function(controlPanelObject) {
		//org.anotherearth.Interface.ensureImplements(controlPanelObject, org.anotherearth.GUIComposite, org.anotherearth.GUIObject);
		controlPanelObjects.add(controlPanelObject);
		fieldset.appendChild(controlPanelObject.getContainingElement());
	};
	this.createIterator = function() {
		return controlPanelObjects.iterator();
	};
	this.performNewEarthPropsUpdate = function() {
	};
	this.performUndoRedoUpdate = function() {
	};
	this.removeChild = function(controlPanelObject) {
		controlPanelObjects.remove(controlPanelObjects.getIndexOf(controlPanelObject));
	};
	this.setTabIndex = function(tabIndex) {//Do nothing with this, and return tabIndex as supplied to indicate that nothing has been done.
		return tabIndex;
	};
	this.show = function() {
		fieldset.style.display = 'block';
	};
	this.hide = function() {
		fieldset.style.display = 'none';
	};
	this.getContainingElement = function() {
		return fieldset;
	};

	//constructor
	this.createGUIElements();
};*/
