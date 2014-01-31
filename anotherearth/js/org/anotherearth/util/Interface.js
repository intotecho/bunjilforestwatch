/*for dev testing only, remove from prod code

org.anotherearth.util.Interface = function(name, methods) {//constructor
	if(arguments.length != 2) {
		throw new Error("Interface constructor called with " + arguments.length
				+ "arguments, but expected exactly 2.");
	}

	this.name = name;
	this.methods = [];

	for(var i = 0, len = methods.length; i < len; i++) {
		if(typeof methods[i] !== 'string') {
				throw new Error("Interface constructor expects method names to be " 
						+ "passed in as a string.");
		}
		this.methods.push(methods[i]);        
	}    
}; 

   
org.anotherearth.util.Interface.ensureImplements = function(object) {// Static class method.
	if(arguments.length < 2) {
		throw new Error("Function Interface.ensureImplements called with " + 
				arguments.length  + "arguments, but expected at least 2.");
	}

	for(var i = 1, len = arguments.length; i < len; i++) {
		var thisInterface = arguments[i];//interface is a keyword reserved for later use
		if(thisInterface.constructor !== org.anotherearth.util.Interface) {
			throw new Error("Function Interface.ensureImplements expects arguments "   
					+ "two and above to be ges of Interface.");
		}

		for(var j = 0, methodsLen = thisInterface.methods.length; j < methodsLen; j++) {
			var method = thisInterface.methods[j];
			if(!object[method] || typeof object[method] !== 'function') {
				throw new Error("Function Interface.ensureImplements: " + object 
						+ "does not implement the " + thisInterface.name 
						+ " thisInterface. Method " + method + " was not found.");
			}
		}
	} 
};
*/
