//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.model = window.org.anotherearth.model || {};

//FIXME this class's functionality should be subsumed within the model class - in large part this class runs counter to principle of asking class with information to do work for you
org.anotherearth.model.URLManager = {};
org.anotherearth.model.URLManager.createURLFromCurrentParameters = function(LEarth, REarth, earthsManager) {//static method
		var LEarthProps = LEarth.getProperties();
		var REarthProps = REarth.getProperties();
		var parameters = {};
		parameters.LLat  = LEarthProps.lat;
		parameters.LLng  = LEarthProps.lng;
		parameters.LAlt  = LEarthProps.alt;
		parameters.LTilt = LEarthProps.tilt;
		parameters.LHead = LEarthProps.head;
		parameters.LDate = LEarthProps.date;
		parameters.RLat  = REarthProps.lat;
		parameters.RLng  = REarthProps.lng;
		parameters.RAlt  = REarthProps.alt;
		parameters.RTilt = REarthProps.tilt;
		parameters.RHead = REarthProps.head;
		parameters.RDate = REarthProps.date;
		parameters.isTiltLocked    = (earthsManager.getIsTiltLocked())          ? 1 : 0;
		parameters.isHeadingLocked = (earthsManager.getIsHeadingLocked())       ? 1 : 0;
		parameters.isAltLocked     = (earthsManager.getIsVertMovementLocked())  ? 1 : 0;
		parameters.isLatLngLocked  = (earthsManager.getIsHorizMovementLocked()) ? 1 : 0;
		var url = location.protocol + '//' + location.host + location.pathname;

		var _getSeparator = function() {
			_getSeparator = function() {//This changes _getSeparator() from a function returning "?" to one returning "&".
				return "&";               //I.e. for the first call, ? is returned, then subsequently &.
			};
			return "?";
		};

		for (var parameter in parameters) {
			if (parameters.hasOwnProperty(parameter)) {
				url += _getSeparator() + parameter + "=" +  parameters[parameter];
			}
		}

		return url;
};
org.anotherearth.model.URLManager.getURLQueryStringValue = function(queryStringArg) {//static method
	var valueArgPair = new RegExp(queryStringArg + '=([-,\\d\.]*)');
	var matches = location.search.match(valueArgPair);
	if (matches !==  null) {
		return matches[1];
	}
	else {
		return null;
	}
};
