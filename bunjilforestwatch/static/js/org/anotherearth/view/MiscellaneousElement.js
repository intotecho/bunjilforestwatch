//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

//with reference to the composite design pattern, a leaf class
//implements GUIObject, GUIComposite
//wrapper class allowing html to be added to composite structure
org.anotherearth.view.MiscellaneousElement = function(html) {
	//private variables
	var element = html;
	
	//privileged methods
	this.createGUIElements = function(html) {
		element = html;
	};
	this.createIterator = function() {//null Iterator
		return {next: function() {
	           		return null; 
		       },
		       hasNext: function() {
			   		return false;
		       }
		}; 
	};
	this.getContainingElement = function() {
		return element;
	};
	this.setTabIndex = function(tabIndex) {//Do nothing with this, and return tabIndex as supplied to indicate that nothing has been done.
		return tabIndex;
	};
	this.show = function() {
		element.style.display = 'block';
	};
	this.hide = function() {
		element.style.display = 'none';
	};
	
	//constructor
	this.createGUIElements(html);
};
org.anotherearth.view.MiscellaneousElement.prototype = {
	addChild: function() {},
	removeChild: function() {}
};
