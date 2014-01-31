//This file must typically be included first, as the intention is that other classes reference it as through it were a native language entity
//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.util = window.org.anotherearth.util || {};

org.anotherearth.util.ArrayList = function() {
	//constructor
	var buffer = [];
	var args = arguments;
	if (args.length > 0) {
		this.buffer = args[0];
	}

	//inner class
	var _Iterator = function (buffer) {
		var table = buffer;
		var len = buffer.length;
		var index = 0;

		this.hasNext = function() {
			return (index < len);
		};

		this.next = function() {
			if (this.hasNext()) {
				return table[index++];
			}
			else {
				return null;
			}
		};
	};

	//privileged methods
	this.add = function(object) {
		buffer.push(object);
	};
	this.getLength = function() {
		return buffer.length;
	};
	this.indexOf = function(object) {
		for (var i = 0; i <= buffer.length; i++) {
			if (buffer[i] === object) {
				break;
			}
		}
		return i;
	};
	this.iterator = function() {
		return new _Iterator(buffer);//TODO: don't like creating a new one each time
	};
	this.remove = function(index) {
		buffer.splice(index, 1);
	};
}; 
