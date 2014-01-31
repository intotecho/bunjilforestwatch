//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.util = window.org.anotherearth.util || {};

org.anotherearth.util.NullIterator = function() {};
org.anotherearth.util.NullIterator.prototype = {
	next: function() {
		return null;
	},
	hasNext: function() {
		return false;
	}
};
