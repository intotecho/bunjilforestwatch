//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order
//
org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

//implements GUIWidget and by extension GUIObject, TwoEarthsObserver and GUIComposite
org.anotherearth.view.TwoEarthsCheckbox = function(checkboxLabel, checkboxId, earthModel) {
	//private variables
	var containingElement, checkbox, onClickCommand, newEarthPropsUpdateStrategy, undoRedoUpdateStrategy;
	var checkboxLabel = checkboxLabel;
	var checkboxId    = checkboxId;
	var earthModel    = earthModel;

	//privileged methods
	this.addClickEventListener = function(command) {
		onClickCommand = command;//for programmatic calls to setIsChecked()
		$(checkbox).bind('click', function() {
			command.execute();
		});
	};
	this.createGUIElements = function() {
		containingElement = document.createElement('div');
		$(containingElement).addClass('control_panel_element');
		containingElement.id = checkboxId + "_checkbox_container";//TODO: could improve this id strategy?
		checkbox = document.createElement('input');
		checkbox.type = 'checkbox';
		checkbox.id = checkboxId;

		var labelElement = document.createElement('label');
		labelElement.setAttribute('for', checkboxId);
		labelElement.innerHTML = checkboxLabel;

		containingElement.appendChild(checkbox);
		containingElement.appendChild(labelElement);
		containingElement.style.display = 'none';
	};
	this.createIterator = function() {//null Iterator
		return {next:    function() { return null;  },
		        hasNext: function() { return false; }
		       }; 
	};
	this.getIsChecked = function() {
		return $(checkbox).attr('checked');
	};
	this.getContainingElement = function() {
		return containingElement;
	};
	this.setIsChecked = function(newIsChecked){
		var oldIsChecked = this.getIsChecked();
		if (newIsChecked == oldIsChecked) {
			return;
		}
		(oldIsChecked)? $(checkbox).attr('checked', 'true') : $(checkbox).attr('checked', 'false');
		onClickCommand.execute();
	};
	this.show = function() {
		containingElement.style.display = 'block';
	};
	this.hide = function() {
		containingElement.style.display = 'none';
	};
	this.performUndoRedoUpdate = function() {
		undoRedoUpdateStrategy.execute(this);
	};
	this.performNewEarthPropsUpdate = function() {
		newEarthPropsUpdateStrategy.execute(this);
	};
	this.setUndoRedoUpdateStrategy = function(strategy) {
		undoRedoUpdateStrategy = strategy;
	};
	this.setNewEarthPropsUpdateStrategy = function(strategy) {
		newEarthPropsUpdateStrategy = strategy;
	};
	this.setTabIndex = function(tabIndex) {
		checkbox.setAttribute('tabindex', tabIndex++);
		return tabIndex;
	};

	//constructor
	this.createGUIElements();
	onClickCommand = { execute: function() {} };
	undoRedoUpdateStrategy      = { execute: function(button) {} };//null strategies
	newEarthPropsUpdateStrategy = { execute: function(button) {} };
};
org.anotherearth.view.TwoEarthsCheckbox.prototype = {
	addChild: function() {},//Composite classes alone implements these methods - this is a leaf class.
	removeChild: function(){}
};
