//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

//implements GUIWidget and by extension GUIObject, TwoEarthsObserver and GUIComposite
//Composite leaf class
org.anotherearth.view.RadioButtons = function(radioButtons, groupId) {
	var radioButtons = radioButtons;
	var groupId = groupId;
	var onClickCommand, containingElement;
	var newEarthPropsUpdateStrategy, undoRedoUpdateStrategy;

	//privileged methods
	this.addClickEventListener = function(command) {
		onClickCommand = command;//for programmatic calls to setIsChecked()       

		for (var button in radioButtons) {
			if (radioButtons.hasOwnProperty(button)) {
				if (typeof document.body.style.maxHeight === 'undefined') {//if IE6 - IE6 doesn't register radio button clicks visibly otherwise
					$(radioButtons[button].htmlElement).click(function() {
						var name = this.getAttribute('name');
						$("input[name='" + name + "']").removeAttr('checked');
						$(this).attr('checked', 'checked');
						command.execute(this);
					});
				}
				else {
					$(radioButtons[button].htmlElement).click(function() {
						command.execute(this);
					});
				}
			}		
		}
	};
	this.createGUIElements = function() {
		containingElement = document.createElement('div');
		$(containingElement).addClass('control_panel_element');
		containingElement.id = groupId + "_container";//TODO: could improve this id strategy?
		for (var i = 0; i < radioButtons.length; i++) {
			var label = document.createElement('label');
			label.setAttribute('for', radioButtons[i].id);
			var input   = document.createElement('input');
			input.type  = 'radio';
			input.id    = radioButtons[i].id;
			input.name  = radioButtons[i].name;
			input.value = radioButtons[i].value;
			radioButtons[i].htmlElement = input;

			label.appendChild(input);
			var textSpan = document.createElement('span');
			$(textSpan).addClass('radio_button_label_span');
			textSpan.appendChild(document.createTextNode(radioButtons[i].label));
			label.appendChild(textSpan);
			containingElement.appendChild(label);
		}
		containingElement.style.display = 'none';
	};
	this.createIterator = function() {//null Iterator
		return {next:    function() { return null;  },
		        hasNext: function() { return false; }
		       }; 
	};
	this.getContainingElement = function() {
	  return containingElement;
	};
	this.getIsChecked = function(index) {
		return $(radioButtons[index].htmlElement).attr('checked');
	};
	this.getIndexOf = function(value) {
		var i = 0;
		for (var button in radioButtons) {
			if (radioButtons.hasOwnProperty(button) && radioButtons[button].value === value) {
				break;
			}	
		}
		return i;
	};
	this.performUndoRedoUpdate = function() {
		undoRedoUpdateStrategy.execute(this);
	};
	this.performNewEarthPropsUpdate = function() {
		newEarthPropsUpdateStrategy.execute(this);
	};
	this.setIsChecked = function(newIsChecked, index) {
		var oldIsChecked = this.getIsChecked(index);
		if (newIsChecked === oldIsChecked) {
			return;
		}
		(oldIsChecked)? $(radioButtons[index].htmlElement).attr('checked', 'true') : $(radioButtons[index].htmlElement).attr('checked', 'false');
		onClickCommand.execute(radioButtons[index]);
	};
	/*this.setIsEnabled = function(newIsEnabled) {//TODO: improve this
		var oldIsEnabled = isEnabled;
		if(oldIsEnabled === newIsEnabled) {
			return;
		}
		if (newIsEnabled) {
			$(containingElement, input).removeAttr('disabled').removeClass('ui-state-disabled');
		}
		else {
			$(containingElement, input).attr('disabled', 'disabled').removeClass('ui-state-hover').removeClass('ui-state-focus').addClass('ui-state-disabled');
		}
	};*/
	this.setTabIndex = function(tabIndex) {
		for (var i = 0; i < radioButtons.length; i++) {
			radioButtons[i].htmlElement.setAttribute('tabindex', tabIndex++);
		}
		return tabIndex;
	};
	this.show = function() {
		containingElement.style.display = 'block';	
	};
	this.hide = function() {
		containingElement.style.display = 'none';	
	};
	this.setNewEarthPropsUpdateStrategy = function(strategy) {
	  newEarthPropsUpdateStrategy = strategy; 
	};
	this.setUndoRedoUpdateStrategy = function(strategy) {
	  undoRedoUpdateStrategy = strategy;
	};
	
	//constructor
	this.createGUIElements();
	onClickCommand = function() { this.execute = function() {}; };
	undoRedoUpdateStrategy      = {execute: function(button) {} };
	newEarthPropsUpdateStrategy = {execute: function(button) {} };
};
org.anotherearth.view.RadioButtons.prototype = {
	addChild:    function() {},//Composite classes alone implements these methods - this is a leaf class.
	removeChild: function() {}//TODO: throw unsupported method?
};
