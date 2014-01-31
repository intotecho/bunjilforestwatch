//necessarily three classes in this file, as the latter two classes are both composed of one of the preceding classes

//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

//Composite pattern leaf class
//implements GUIComposite, GUIWidget and by extension GUIObject
org.anotherearth.view.SimpleButton = function(buttonLabel, buttonId, model) {
	//private variables
	var containingElement, button, isEnabled;
	var buttonId = buttonId;
	var buttonLabel = buttonLabel;
	var model = model;

	//privileged methods
	this.createGUIElements = function() {
		containingElement = document.createElement('div');
		$(containingElement).addClass('control_panel_element');
		containingElement.id = buttonId + "_button_container";

		button = document.createElement('button');
		button.id = buttonId;
		$(button).addClass('ui-state-default');
		$(button).attr("innerHTML", buttonLabel);
		//TODO: room for abstracting further into GUIElement class e.g. event listeners
		$(button).mouseenter(function() {
			$(this).toggleClass('ui-state-hover');
		});
		$(button).mouseleave(function() {
			$(this).toggleClass('ui-state-hover');
			$(this).removeClass('ui-state-active');
		});
		$(button).bind('mousedown mouseup', function() {
			$(this).toggleClass('ui-state-active');
		});
		$(button).bind('focus blur', function() {
			$(this).toggleClass('ui-state-focus');
		});

		containingElement.appendChild(button);
		containingElement.style.display = 'none';
	};

	this.addClickEventListener = function(command) {
		//org.anotherearth.Interface.ensureImplements(command, org.anotherearth.Command);
		$(button).bind('click', function() {
			command.execute();
			return false;//else page reloads if Button in form - suppressing default button action
		});
	};
	this.createIterator = function() {//null Iterator
		return {next:    function() { return null;  },
		        hasNext: function() { return false; }
		       }; 
	};
	this.getContainingElement = function() {
		return containingElement;
	};
	this.getModel = function() {
		return model;
	};
	this.setIsEnabled = function(newIsEnabled) {
		var oldIsEnabled = isEnabled;
		if(oldIsEnabled == newIsEnabled) {
			return;
		}
		if (newIsEnabled) {
			$(button).removeAttr('disabled').removeClass('ui-state-disabled');
		}
		else {
			$(button).attr('disabled', 'disabled').removeClass('ui-state-hover').removeClass('ui-state-focus').addClass('ui-state-disabled');
		}
	};
	this.setTabIndex = function(tabIndex) {
		button.setAttribute('tabindex', tabIndex++);
		return tabIndex;
	};
	this.show = function() {
		containingElement.style.display = 'block';
	};
	this.hide = function() {
		containingElement.style.display = 'none';
	};

	//constructor
	this.createGUIElements();
};
org.anotherearth.view.SimpleButton.prototype = {
	addChild: function() {}, 
	removeChild: function() {}
};

//implements GUIWidget and by extension GUIObject, implements TwoEarthsObserver and GUIComposite
org.anotherearth.view.TwoEarthsButton = function(buttonLabel, buttonId, earthModel) {
	//private variables
	var button, undoRedoUpdateStrategy, newEarthPropsUpdateStrategy;

	//privileged methods
	this.addClickEventListener = function(command) {
		button.addClickEventListener(command);
	};
	this.createGUIElements = function() {
		button.createGUIElements();
	};
	this.createIterator  = function() {
		return button.createIterator();
	};
	this.getContainingElement = function() {
		return button.getContainingElement();
	};
	this.getModel = function() {
		return button.getModel();
	};
	this.performUndoRedoUpdate = function() {
		undoRedoUpdateStrategy.execute(this);
	};
	this.performNewEarthPropsUpdate = function() {
		newEarthPropsUpdateStrategy.execute(this);
	};
	this.setIsEnabled = function(newIsEnabled) {
		button.setIsEnabled(newIsEnabled);
	};
	this.setUndoRedoUpdateStrategy = function(updateStrategy) {
		undoRedoUpdateStrategy = updateStrategy;
	};
	this.setNewEarthPropsUpdateStrategy = function(updateStrategy) {
		newEarthPropsUpdateStrategy = updateStrategy;
	};
	this.show = function() {
		button.show();
	};		
	this.hide = function() {
		button.hide();
	};		
	this.setTabIndex = function(tabIndex) {
		return button.setTabIndex(tabIndex);
	};

	//constructor
	button = new org.anotherearth.view.SimpleButton(buttonLabel, buttonId, earthModel);
	button.createGUIElements();
	undoRedoUpdateStrategy      = { execute: function(button) {} };//null strategies
	newEarthPropsUpdateStrategy = { execute: function(button) {} };
};
org.anotherearth.view.TwoEarthsButton.prototype = {
	addChild: function() {},//composite alone implements these methods
	removeChild: function() {}
};

//non-generic button for displaying parameterized URL link upon button click
//implements GUIWidget and by extension GUIObject, TwoEarthsObserver and GUIComposite
org.anotherearth.view.LinkCreatorButton = function(buttonLabel, buttonId, linkBoxId, earthModel) {
	//private variables
	var button, linkBox, undoRedoUpdateStrategy, newEarthPropsUpdateStrategy;
	var buttonLabel = buttonLabel;
	var buttonId = buttonId;
	var earthModel = earthModel;
	var linkBoxId = linkBoxId;

	//private method
	var _createLinkBox = function() {
		linkBox = document.createElement('input');
		linkBox.setAttribute('type', 'text');
		linkBox.id = linkBoxId; 
		button.getContainingElement().appendChild(linkBox);
		linkBox.style.display = 'none';
	};

	//privileged methods
	this.addLink = function(link) {
		if (typeof linkBox === 'undefined') {
			_createLinkBox();
		}
		linkBox.setAttribute('value', link);
		linkBox.style.display = 'none';//apparently giving a text input field a value automatically changes display to block
	};
	this.addClickEventListener = function(command) {
		button.addClickEventListener(command);
	};
	this.createGUIElements = function() {//creates button but not link box, see below
		button.createGUIElements();
	};
	this.createIterator  = function() {
		return button.createIterator();
	};
	this.getContainingElement = function() {
		return button.getContainingElement();
	};
	this.setIsEnabled = function(newIsEnabled) {
		button.setIsEnabled(newIsEnabled);
	};
	this.setIsLinkVisible = function(newIsLinkVisible) {
		if (typeof linkBox === 'undefined') {
			return;
		}
		var oldIsLinkVisible = (linkBox.style.display === 'block');
		if (oldIsLinkVisible == newIsLinkVisible) {
			return;
		}
		else if (newIsLinkVisible) {
			linkBox.style.display = 'block';
		}
		else {
			linkBox.style.display = 'none';
		}
	};
	this.show = function() {
		button.getContainingElement().style.display = 'block';
		if (typeof linkBox !== 'undefined') {//want to keep linkBox hidden at this point - sorry, bit ugly
			linkBox.style.display = 'none';
		}
	};
	this.hide = function() {
		button.getContainingElement().style.display = 'none';
	};
	this.setTabIndex = function(tabIndex) {
		return button.setTabIndex(tabIndex);
	};
	this.performUndoRedoUpdate = function() {
		undoRedoUpdateStrategy.execute(this);
	};
	this.performNewEarthPropsUpdate = function() {
		newEarthPropsUpdateStrategy.execute(this);
	};
	this.setUndoRedoUpdateStrategy = function(updateStrategy) {
		undoRedoUpdateStrategy = updateStrategy;
	};
	this.setNewEarthPropsUpdateStrategy = function(updateStrategy) {
		newEarthPropsUpdateStrategy = updateStrategy;
	};

	//constructor
	button = new org.anotherearth.view.TwoEarthsButton(buttonLabel, buttonId, earthModel);
	this.createGUIElements();
	undoRedoUpdateStrategy      = { execute: function(button) {} };//null strategies
	newEarthPropsUpdateStrategy = { execute: function(button) {} };
};
org.anotherearth.view.LinkCreatorButton.prototype = {
	addChild: function() {},//composite only implements these
	removeChild: function() {}
};
