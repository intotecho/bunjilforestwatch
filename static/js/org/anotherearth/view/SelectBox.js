//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

//Composite pattern leaf class
org.anotherearth.view.SelectBox = function(options, selectBoxSize, selectBoxText, selectBoxId, isMultipleSelectType) {
	var options = options;//TODO: type checking on these widget elements' arguments - and on the abstract widget elements
	var selectBoxSize = selectBoxSize;
	var selectBoxText = selectBoxText;
	var selectBoxId = selectBoxId;
	var isMultipleSelectType = isMultipleSelectType;//FIXME - a tagged class, which is bad
	var selectBoxId = selectBoxId;
	var onClickCommand, containingElement, selectBox;
	var undoRedoUpdateStrategy, newEarthPropsUpdateStrategy;
	var multipleSelectCheckBoxes = null;

	//privileged methods
	this.addClickEventListener = function(command) {
		onClickCommand = command;
		if (!isMultipleSelectType) {
			for (var option in options) {
				if (options.hasOwnProperty(option)) {
					$(options[option].htmlElement).click(function() {command.execute(selectBox, this);});
				}			
			}
		}
		else {
			multipleSelectCheckBoxes = [];//FIXME wrong to be populating this array here - also, can't I get programmatic access to this widget?
			var re = new RegExp(selectBoxId + '\\d+');//This is the form of id assigned by dropdownlist plugin to checkboxes.
			var inputs = document.getElementsByTagName('input');
			for (var input in inputs) {
				if (typeof inputs[input].id !== 'undefined' && inputs[input].id.match(re)) {
					multipleSelectCheckBoxes.push(inputs[input]);
				}
			}
			$(multipleSelectCheckBoxes).click(function() {command.execute(selectBox, this);});
		}
	};
	this.createGUIElements = function() {
		//define selectbox
		containingElement = document.createElement('div');
		$(containingElement).addClass('control_panel_element').addClass('select_box_container');
		containingElement.id = selectBoxId + "_select_box_container";//TODO: don't like this
		
		selectBox = document.createElement('select');
		selectBox.id = selectBoxId;

		if (isMultipleSelectType) {
			selectBox.setAttribute("multiple", "multiple");
		}
		else {
			var option = document.createElement('option');
			option.setAttribute('selected', 'selected');
			selectBox.appendChild(option);
		}

		//define options
		for (var i = 0; i < options.length; i++) {
			var option   = document.createElement('option');
			option.value = options[i].value;

			option.appendChild(document.createTextNode(options[i].text));
			options[i].htmlElement = option;
			selectBox.appendChild(option);
		}

		var selectBoxLabel = document.createElement('label');
		selectBoxLabel.appendChild(document.createTextNode(selectBoxText));

		containingElement.appendChild(selectBoxLabel);
		containingElement.appendChild(selectBox);
		if (isMultipleSelectType) {       
			$(selectBox).dropdownchecklist();
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
	this.getIsEnabled = function(index) {
		if ($(options[index].htmlElement).attr('disabled') === 'disabled') {
			return false;
		}
		else {
			return true;
		}
	};
	this.getIsSelected = function(index) {
		if ($(options[index].htmlElement).attr('selected') === 'selected') {
			return true;
		}
		else {
			return false;
		}
	};
	this.setIsSelected = function(index, newIsSelected) {
		var oldIsSelected = this.getIsSelected(index);
		if (newIsSelected === oldIsSelected) 
			return;

		var selectedElement;
		if (isMultipleSelectType) {
			selectedElement = $(multipleSelectCheckBoxes[index]);
			(newIsSelected) ? selectedElement.attr('checked', true) : selectedElement.attr('checked', false);
		}
		else {
			selectedElement = $(options[index].htmlElement);
			selectedElement.val(newIsSelected);
		}
		
		onClickCommand.execute(selectBox, options[index]);
	};
	this.performUndoRedoUpdate = function() {
		undoRedoUpdateStrategy.execute(this);
	};
	this.performNewEarthPropsUpdate = function() {
		newEarthPropsUpdateStrategy.execute(this);
	};
	this.getIndexOfOption = function(optionValue) {
		for (var i = 0; i < options.length; i++) {
			if (options[i].value === optionValue) {
				break;
			}
		}
		return i;
	};
	/*
	this.setIsEnabled = function(optionIndex, newIsEnabled) {
	};
	*/
	this.setTabIndex = function(tabIndex) {
		if (!isMultipleSelectType) {
			for (var i = 0; i < options.length; i++) {
				options[i].htmlElement.tabindex =  tabIndex++;
			}
		}
	  return tabIndex;
	};
	this.show = function() {
		containingElement.style.display = 'block';
	};
	this.hide = function() {
		containingElement.style.display = 'none';
		if (isMultipleSelectType) {
			$(selectBox).dropdownchecklist('hide');
		}
	};
	this.hideDropDownList = function() {
		if (isMultipleSelectType) {
			$(selectBox).dropdownchecklist('hide');
		}
	};
	this.setNewEarthPropsUpdateStrategy = function(strategy) {
	  newEarthPropsUpdateStrategy = strategy; 
	};
	this.setUndoRedoUpdateStrategy = function(strategy) {
	  undoRedoUpdateStrategy = strategy;
	};
	
	//constructor
	this.createGUIElements();
	onClickCommand               = function() { this.execute = function() {}; };
	undoRedoUpdateStrategy       = { execute: function(button) {} };
	newEarthPropsUpdateStrategy  = { execute: function(button) {} };
};
org.anotherearth.view.SelectBox.prototype = {
	addChild:    function() {},
	removeChild: function() {}
};
