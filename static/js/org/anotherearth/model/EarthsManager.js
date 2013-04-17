//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.model = window.org.anotherearth.model || {};

org.anotherearth.model.EarthsManager = function() {
	//private variables
	var earthLtoRCamDiffs  = {};
	earthLtoRCamDiffs.lat  = null;
	earthLtoRCamDiffs.lng  = null;
	earthLtoRCamDiffs.alt  = null;
	earthLtoRCamDiffs.tilt = null;
	earthLtoRCamDiffs.head = null;
	var earthRtoLCamDiffs  = {};  //Having two separate collections, the choice of which depends 
	earthRtoLCamDiffs.lat  = null;//upon the camera being moved, produces a performance benefit.
	earthRtoLCamDiffs.lng  = null;
	earthRtoLCamDiffs.alt  = null;
	earthRtoLCamDiffs.tilt = null;
	earthRtoLCamDiffs.head = null;
	var isHorizMovementLocked = false;
	var isVertMovementLocked = false;
	var isTiltLocked = false;
	var isHeadingLocked = false;
	var completeHistory = [];
	var undoHistory = [];                  //When undo is performed, a snapshot of current history is taken and 
	var currentUndoHistoryPosition = null; //traversed through until new movement is performed, at which point 
	var observers = {};                    //undoHistory is cleared and currentUndoHistoryPosition is set back 
	observers.undoRedo = [];               //to null. currentUndoHistoryPosition is relative to the last item 
	observers.newEarthProps = [];          //to the highest index array element. This seems like the most legible
	                                       //undo scheme.
	//privileged methods
	this.redo = function() {
		if (this.getNumberRemainingRedos()) {//If not equal to null and not equal to 0.
			currentUndoHistoryPosition++;
			completeHistory.push(undoHistory[undoHistory.length-1 + currentUndoHistoryPosition]);
			this.notifyUndoRedoObservers();
		}
		else {
			throw new Error("nothing to redo - shouldn't be calling method.");
		}
	};
	this.undo = function() {
		if (currentUndoHistoryPosition !== null) {//History is currently being travelled through.
			if (this.getNumberRemainingUndos()) {   
				currentUndoHistoryPosition--;
			}
			else {
				throw new Error("nothing to undo - shouldn't be calling method.");
			}
		}
		else {
			undoHistory = completeHistory.slice(0);//Beginning a journey through history.
			currentUndoHistoryPosition = -1;
		}
		completeHistory.push(undoHistory[undoHistory.length-1 + currentUndoHistoryPosition]);
		this.notifyUndoRedoObservers();
	};
	this.getNumberRemainingRedos = function() {//TODO: according to Holub should return only booleans or objects	
		return ((currentUndoHistoryPosition === null) ? 0 : -currentUndoHistoryPosition);
	};
	this.getNumberRemainingUndos = function() {//TODO: according to Holub should return only booleans or objects		
		return ((currentUndoHistoryPosition === null) ? completeHistory.length-1 : undoHistory.length-1 + currentUndoHistoryPosition);
	};
	this.getCurrentCameraProperties = function() {
		return completeHistory[completeHistory.length-1];
	};
	this.saveCameraProperties = function(LEarthCamProps, REarthCamProps, isCurrentPropertySetOverwritten) {
		var propsToSave = {};
		propsToSave.leftEarth  = LEarthCamProps;
		propsToSave.rightEarth = REarthCamProps;
		undoHistory = [];                 //Saving new properties, as opposed to getting them from history,
		currentUndoHistoryPosition = null;//clears undo stack - history is no longer being examined.
		if (isCurrentPropertySetOverwritten) {
			completeHistory.pop();
		}
		completeHistory.push(propsToSave);
		this.notifyNewEarthPropsObservers();
	};
	this.getLtoRCameraPropertyDifferences = function() {
		return earthLtoRCamDiffs;
	};
	this.getRtoLCameraPropertyDifferences = function() {
		return earthRtoLCamDiffs;
	};
	this.getIsHorizMovementLocked = function() {
		return isHorizMovementLocked;
	};
	this.getIsVertMovementLocked = function() {
		return isVertMovementLocked;
	};
	this.getIsTiltLocked = function() {
		return isTiltLocked;
	};
	this.getIsHeadingLocked = function() {
		return isHeadingLocked;
	};
	this.setIsHorizMovementLocked = function(newIsMovementLocked) {
		isHorizMovementLocked = newIsMovementLocked;
	};
	this.setIsVertMovementLocked = function(newIsMovementLocked) {
		isVertMovementLocked = newIsMovementLocked;
	};
	this.setIsTiltLocked = function(newIsMovementLocked) {
		isTiltLocked = newIsMovementLocked;
	};
	this.setIsHeadingLocked = function(newIsMovementLocked) {
		isHeadingLocked = newIsMovementLocked;
	};
	this.setCameraCoordDiff = function(lockType, value) {
		if (value === null) {
			earthLtoRCamDiffs[lockType] = null;
			earthRtoLCamDiffs[lockType] = null;
		}
		else {
			earthLtoRCamDiffs[lockType] = value;
			earthRtoLCamDiffs[lockType] = -value;
		}
	};
	this.registerUndoRedoObserver = function(observer) {
		//org.anotherearth.util.Interface.ensureImplements(observer, org.anotherearth.TwoEarthsObserver);
		observers.undoRedo.push(observer);
	};
	this.registerNewEarthObserver = function(observer) {
		//org.anotherearth.util.Interface.ensureImplements(observer, org.anotherearth.TwoEarthsObserver);
		observers.newEarthProps.push(observer);
	};
	this.notifyUndoRedoObservers = function() {
		for (var observerNumber in observers.undoRedo) {
			if (observers.undoRedo.hasOwnProperty(observerNumber)) {
				var observer = observers.undoRedo[observerNumber];
				observer.performUndoRedoUpdate();
			}
		}
	};
	this.notifyNewEarthPropsObservers = function() {
		for (var observerNumber in observers.newEarthProps) {
			if (observers.newEarthProps.hasOwnProperty(observerNumber)) {
				var observer = observers.newEarthProps[observerNumber];
				observer.performNewEarthPropsUpdate();
			}
		}
	};
};
