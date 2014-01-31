//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

//wrapper class for plugin
org.anotherearth.view.LockableEarth = function(canvasDivId, earthsController, initialEarthProperties) {
	//private variables
	var ALTITUDE_TYPE;
	var REGULAR_FLY_TO_SPEED = 3.5;
	var ge;
	var geView, geWindow, geOptions, geLayerRoot, geTime;
	var overlays = {};
	var isNextViewChangeIgnored    = false;
	var isNextViewChangeEndIgnored = false;
	var self = this;
	var canvasDivId = canvasDivId;
	var earthCanvas;
	var currentKmlObject;
	var kmlUrl = kmlUrl;
	var isHistoricalImageryEnabled;

	//private class
	var _KmlLoadedCallback = function(callback) {
		var callback;

		this.set = function(newCallback) {
			callback = newCallback;
		};
		this.enact = function(kmlObject) {//if kml overlay is applied  		
			if (kmlObject) {
				currentKmlObject = kmlObject;
				ge.getFeatures().appendChild(kmlObject);
			
				if (kmlObject.getAbstractView() !== null) {
					ge.getView().setAbstractView(kmlObject.getAbstractView());
				}
			}
			callback();
		};	
		//constructor
		this.set(callback);
	};

	//private functions
	var _fetchKml = function(callback) {
		google.earth.fetchKml(ge, kmlUrl, callback.enact);
	};	
	
	var _initEarth = function(instance) {//constructor
		ge = instance;
		geView      = instance.getView();
		geWindow    = instance.getWindow();
		geOptions   = instance.getOptions();
		geLayerRoot = instance.getLayerRoot();
		geTime      = instance.getTime();
		
		ge.getNavigationControl().setVisibility(ge.VISIBILITY_AUTO);
		ALTITUDE_TYPE = ge.ALTITUDE_ABSOLUTE;
		geOptions.setScaleLegendVisibility(true);
		geOptions.setStatusBarVisibility(true);

		//terrain layer enabled by default
		geLayerRoot.enableLayerById(ge.LAYER_ROADS, true);	
		geLayerRoot.enableLayerById(ge.LAYER_BORDERS, true);	
		geLayerRoot.enableLayerById(ge.LAYER_BUILDINGS, true);	
		geLayerRoot.enableLayerById(ge.LAYER_BUILDINGS_LOW_RESOLUTION, true);
			
		overlays.borders        = geLayerRoot.getLayerById(ge.LAYER_BORDERS);
		overlays.roads          = geLayerRoot.getLayerById(ge.LAYER_ROADS);
		overlays.terrain        = geLayerRoot.getLayerById(ge.LAYER_TERRAIN);
		overlays.hiResBuildings = geLayerRoot.getLayerById(ge.LAYER_BUILDINGS);
		overlays.loResBuildings = geLayerRoot.getLayerById(ge.LAYER_BUILDINGS_LOW_RESOLUTION);

		for (var overlay in overlays) {
			if (overlays.hasOwnProperty(overlay)) {
				overlays[overlay].setVisibility(false);
			}
		}

		self.setProperties(initialEarthProperties.lat,
		                   initialEarthProperties.lng,
		                   initialEarthProperties.alt,
		                   initialEarthProperties.tilt,
		                   initialEarthProperties.head,
		                   false,
		                   initialEarthProperties.date);
		earthsController.saveCameraProperties(false);//this method won't do anything when called by first map to be initialized
		geWindow.setVisibility(true);

		//Saving scheme: on viewchangeend (which can be fired continuously, e.g. throughout heading changes) on map that initialized movement,
		//attempt to save Earths' coordinates. If first viewchangeend since mouseup, then save new set of coords;
		//if a suitable interval has elapsed since last viewchangeend also save - this latter condition covers nav control-triggered movement,
		//necessary since nav control doesn't fire events. If neither of the above is true then overwrite the previous set of saved coordinates.
		//Add Event Listeners to Earth
		google.earth.addEventListener(geWindow, 'mouseup', function() {
			earthsController.respondToMouseUpOnEarth();
		});
		google.earth.addEventListener(geView, 'viewchange', function() {
			var moveInitializingEarth = earthsController.getMoveInitializingEarth();
			if (isNextViewChangeIgnored) {
				isNextViewChangeIgnored = false;
				return;
			}
			if (moveInitializingEarth === null) {
				earthsController.setMoveInitializingEarth(self);
			}
			else if (moveInitializingEarth !== self) {//this is a catch for rare instances, happening exclusively during synchronized dragging,
				return;                               //in which a camera moves twice after it has had its position set, thereby bypassing the
			}                                         //movement-ignoring condition above and typically causing movement to abruptly halt.
			                                          //since the movement-ignoring condition is used for other types of movement (other than dragging)
													  //it has not been replaced by this commented condition.
			earthsController.moveOtherEarthIfLocked(self);
		});
		google.earth.addEventListener(geView, 'viewchangeend', function() {
			var moveInitializingEarth = earthsController.getMoveInitializingEarth();
			if (isNextViewChangeEndIgnored) {
				isNextViewChangeEndIgnored = false;
				return;
			}
			if (moveInitializingEarth !== self) {
				return;
			}
			var isCurrentPropSetOverwritten = !earthsController.getIsTimeElapsedSufficientForSave();
			earthsController.saveCameraProperties(isCurrentPropSetOverwritten);
		});
		earthsController.respondToEarthFullyLoading();
	};
	
	var _initEarthFailed = function(errorCode){//this function is mandatory for loading the plugin but unnecessary for me
	};
	
	var _createEarthCanvas = function() {
		earthCanvas = document.createElement('div');
		earthCanvas.id = canvasDivId;
		$(earthCanvas).addClass(org.anotherearth.EARTH_CANVAS_CLASS);
		$('body').append(earthCanvas);
	};
	
	var _getEarthDate = function() {
		  var tp = geTime.getTimePrimitive();
		  var time;

		  if (tp.getType() == 'KmlTimeSpan') {
			  time = tp.getBegin().get();
		  } else {
			  time = tp.getWhen().get();
		  }

		  var re = new RegExp("^(\\d{4})-(\\d{2})-(\\d{2})");

		  var regExMatches = time.match(re);
		  return regExMatches[0];
	};

	//privileged methods
	//TODO should just pass in properties object
	this.setProperties = function(lat, lng, alt, tilt, head, isNextMoveIgnored, date) {
		if (typeof geView === 'undefined') {
			var errorMessage = canvasDivId + " not initialized";
			throw new ReferenceError(errorMessage);
		}
		
		var camera = geView.copyAsCamera(ALTITUDE_TYPE);
		
		if (isNextMoveIgnored) {//e.g. if earths are locked together, this will prevent an infinite loop of property setting between the Earths
			isNextViewChangeIgnored    = true;
			isNextViewChangeEndIgnored = true;
		}
		
		camera.setLatitude(lat);
		camera.setLongitude(lng);
		camera.setAltitude(alt);
		camera.setTilt(tilt);
		camera.setHeading(head);
		geOptions.setFlyToSpeed(ge.SPEED_TELEPORT);
		geView.setAbstractView(camera);
		geOptions.setFlyToSpeed(REGULAR_FLY_TO_SPEED);
		
		//putting date setting last in case that historical data for the original location differs from that for the new location,
		//assuming this matters
		if (date !== null) {
			var timeStamp = ge.createTimeStamp("");
			timeStamp.getWhen().set(date);		
			geTime.setTimePrimitive(timeStamp);
		}
	};
	
	this.getProperties = function() {
		if (typeof geView === 'undefined') {//i.e. if earth not loaded
			var errorMessage = canvasDivId + " not initialized";
			throw new ReferenceError(errorMessage);
		}
		else {
			var props = {};
			var camera    = geView.copyAsCamera(ALTITUDE_TYPE);	
			
			//Props given to six decimal places - any more precision unnecessary even at lowest altitudes.
			var oneMillion = Math.pow(10,6);
			props.lat  = Math.round(camera.getLatitude()  * oneMillion)/oneMillion;
			props.lng  = Math.round(camera.getLongitude() * oneMillion)/oneMillion;
			props.alt  = Math.round(camera.getAltitude()  * oneMillion)/oneMillion;
			props.tilt = Math.round(camera.getTilt()      * oneMillion)/oneMillion;
			props.head = Math.round(camera.getHeading()   * oneMillion)/oneMillion;
			
			props.date = _getEarthDate();
			
			return props;
		}
	};
	
	this.toggleExtra = function(overlayId) {
		//TODO this should be populated from an enum equivalent within this class
		switch(overlayId) {
			case 'atmosphere' :
				geOptions.setAtmosphereVisibility(!geOptions.getAtmosphereVisibility());
				break;
			case 'hiRes':
				overlays.hiResBuildings.setVisibility(!overlays.hiResBuildings.getVisibility());
				break;
			case 'loRes':
				overlays.loResBuildings.setVisibility(!overlays.loResBuildings.getVisibility());
				break;
			case 'borders':
				overlays.borders.setVisibility(!overlays.borders.getVisibility());
				break;
			case 'grid':
				geOptions.setGridVisibility(!geOptions.getGridVisibility());
				break;
			case 'roads':
				overlays.roads.setVisibility(!overlays.roads.getVisibility());
				break;
			case 'sun':
				var sun = ge.getSun();
				sun.setVisibility(!sun.getVisibility());
				break;
			case 'terrain':
				overlays.terrain.setVisibility(!overlays.terrain.getVisibility());
				break;
			case 'time':
				var timeControl = geTime.getControl();
				if (geTime.getHistoricalImageryEnabled()) {
					timeControl.getVisibility() ? timeControl.setVisibility(ge.VISIBILITY_HIDE) : timeControl.setVisibility(ge.VISIBILITY_SHOW);
				}
				else if (timeControl.getVisibility()) {
					timeControl.setVisibility(false);
				}
				else {
					geTime.setHistoricalImageryEnabled(true);
				}
				break;
			default:
				var errorMessage = 'Unrecognised Overlay Type: ' + overlayId;
				var error = new Error();
				error.message = errorMessage;
				throw error;
		}
	};
	this.createEarthInstance = function() {
		google.earth.createInstance(canvasDivId, _initEarth, _initEarthFailed);
	};
	this.setCanvasPositionAndSize = function(top, left, width, height) {
		$(earthCanvas).css('top', top).css('left', left).css('width', width).css('height', height);
	};
	this.addKmlFromUrl = function(newKmlUrl, newKmlLoadedCallback) {
		kmlLoadedCallback = new _KmlLoadedCallback(newKmlLoadedCallback);
		if (currentKmlObject) {
			if (ge) {
				ge.getFeatures().removeChild(currentKmlObject);
			}
			currentKmlObject = null;
		}
		kmlUrl = newKmlUrl;
		if (typeof ge !== 'undefined') {
			_fetchKml(kmlLoadedCallback);
		}
	};
	this.show = function() {
		earthCanvas.style.display = 'block';
	};

	//constructor
	_createEarthCanvas();
};
