/**
 * @name base=drawing-tools.js
 * @version 1.0
 * @author Chris Goodman
 * @copyright (c) Copyright (c) 2013 Licences: Creative Commons Attribution
 * @fileoverview Displays the google Drawing Manager tool bar on a map with
 *               minor customisations.
 */

/* global CodeMirror */
/* global initialize_map */

function showDropPanel(e) {
	"use strict";
	e.stopPropagation();
	e.preventDefault();
	$('#drop-container').show();
	return false;
}

function hideDropPanel(e) {
	"use strict";
	if(e !== undefined) {
		e.stopPropagation();
		e.preventDefault();
	}
	$('#drop-container').hide();
	return false;
}


/**
 * 
 * These tools are based on example by Joshua Lau -
 * https://google-developers.appspot.com/maps/documentation/utils/geojson/
 * 
 * @param map a google map
 * @param mapContainer div containing the map
 * @param dropContainer div containing the drop area
 * @param geoJsonPanel div for displaying geojson
 * @param geoJsonInput div for inputing geojson
 * @param downloadLink download geojson button
 */
function DrawingTools(map_p, mapContainer_p, dropContainer_p, geoJsonPanel_p, geoJsonInput_p, downloadLink_p) {
	"use strict";
	// Initialize the map.
	this.mapContainer = mapContainer_p;
	this.dropContainer = dropContainer_p;
	this.geoJsonPanel = geoJsonPanel_p;
	this.geoJsonInput = geoJsonInput_p;
	this.downloadLink = downloadLink_p;
	
	//map_p.data.setControls([ 'Point', 'Polygon' ]);
	var styleOptions = areaBoundaryPolygonOptions;
	styleOptions.editable = true;
	styleOptions.draggable = true;
	styleOptions.fillOpacity =  0.5;  //more opacity when drawing.
	
	map_p.data.setStyle(styleOptions);
	map_p.data.setOptions({
		drawingControl: false,
		drawingMode: null,
		controls : null,
		position: google.maps.ControlPosition.TOP_CENTER,
	});
	
	this.map = map_p;
	
	this.map.mode = "none";

	this.bindDataLayerListeners();

	var geoJsonInputRect = this.geoJsonInput.getBoundingClientRect();
	var panelRect = this. geoJsonPanel.getBoundingClientRect();
	this.geoJsonInput.style.height = panelRect.bottom - geoJsonInputRect.top - 8 +
			 "px";
	
	$("#map-canvas-c").on("dragover", function(event) {
		//console.log("dragover map");
		showDropPanel(event);
	});

	$("#map-canvas-c").on("drop", function(event) {
		console.log("drop map");
		hideDropPanel(event);
	});

	$("#drop-container").on("dragover", function(event) {
		//console.log("dragover drop-container");
		showDropPanel(event);
	});

	$("#drop-container").on("dragleave", function(event) {
		//console.log("dragleave drop-container");
		hideDropPanel(event);
	});

	$("#drop-container").on("drop", function(event) {
		console.log("drop drop-container " + event.target);
		handleDrop(event, initialize_map.map);
	});
	//this.refreshDataFromGeoJson();
	
	// Set up events for changing the geoJson input.
	google.maps.event.addDomListener(this.geoJsonInput, 'input',
			this.refreshDataFromGeoJson.bind(this));
	google.maps.event.addDomListener(this.geoJsonInput, 'input',
			this.refreshDownloadLinkFromGeoJson.bind(this));

	// Set up events for styling.
	//google.maps.event.addDomListener(window, 'resize', this.resizeGeoJsonInput);
}

DrawingTools.drawingTools = null;

//Apply listeners to refresh the GeoJson display on a given data layer.
DrawingTools.prototype.bindDataLayerListeners = function () {
	"use strict";
	this.map.data.addListener('addfeature', this.refreshGeoJsonFromData.bind(this));
	this.map.data.addListener('addfeature', this.fitMapToGeoJsonFromData);
	this.map.data.addListener('removefeature', this.refreshGeoJsonFromData.bind(this));
	this.map.data.addListener('setgeometry', this.refreshGeoJsonFromData.bind(this));
};


/**
 * Create a data layer for points.
 * Give it a function to call when a point is marker is added.
 */
DrawingTools.prototype.drawCenterPointMarker  = function (stop_handler) {
	"use strict";
	
	//this.removeCenterPointMarker();
	
	var newData = new google.maps.Data({
		map : this.map,
		style : this.map.data.getStyle(),
		editable: true,
		controls : null, //['Point'],
		drawingMode: 'Point'
	});
	this.map.data.setMap(null);
	this.map.data = newData;
	this.bindDataLayerListeners();
	this.setGeoJsonValidity(true, null);
	//this.map.setOptions({
	//		disableDefaultUI: true // no drawing controls
	//});
	this.map.mode = 'drawCenterPointMarker';
	
	this.map.data.addListener('addfeature', stop_handler);
};

DrawingTools.prototype.stopDrawCenterPointMarker=function () {
	"use strict";
	var map = this.map;
	
	map.data.setOptions({
		drawingControl: false,
		drawingMode: null
		//disableDefaultUI: false// no drawing controls
	});
		
	map.data.toGeoJson(function(geoJson) {
		map.drawingTools.area_location = geoJson;
	});
	
	map.mode = 'none';
};

DrawingTools.prototype.removeCenterPointMarker=function () {
	"use strict";
	this.map.data.setMap(null);
	this.bindDataLayerListeners();
	this.setGeoJsonValidity(true, null);
};



/**
 * Create a data layer for points.
 * Give it a function to call when a point is marker is added.
 */
DrawingTools.prototype.drawPolygon  = function (stop_handler) {
	"use strict";
	
	//this.removePolygon();
	/* global areaBoundaryPolygonOptions */ 
	
	var newData = new google.maps.Data({
		map : this.map,
		style : this.map.data.getStyle(),
		editable: true,
		controls : null, //['Polygon'],
		drawingMode: 'Polygon',
		drawingControl: false,
		polygonOptions: areaBoundaryPolygonOptions
	});
	this.map.data.setMap(null);
	this.map.data = newData;
	this.bindDataLayerListeners();
	this.setGeoJsonValidity(true, null);
	//this.map.setOptions({
	//		disableDefaultUI: true // no drawing controls
	//});
	this.map.mode = 'drawPolygon';
	
	this.map.data.addListener('addfeature', stop_handler);
};

DrawingTools.prototype.stopDrawPolygon=function () {
	"use strict";
	var map = this.map;
	
	map.data.setOptions({
		drawingControl: false,
		drawingMode: null
		//disableDefaultUI: false// no drawing controls
	});
	
	this.refreshDataFromGeoJson();
	this.refreshGeoJsonFromData();
	
	map.data.toGeoJson(function(geoJson) {
		map.drawingTools.boundary = geoJson;
	});
	
	map.mode = 'none';
};

DrawingTools.prototype.removePolygon=function () {
	"use strict";
	this.map.data.setMap(null);
	this.bindDataLayerListeners();
	this.setGeoJsonValidity(true, null);
};

//Refresh different components from other components.
DrawingTools.prototype.refreshGeoJsonFromData = function (e) {
	"use strict";
	//console.log(e);
	var map = this.map;  //context of this about to change in next call.
	map.data.toGeoJson(function(geoJson) {
		var txt = JSON.stringify(geoJson, null, 2);
		var editor = initialize_map.editor;
		if (typeof editor !== 'undefined') {
			initialize_map.editor.setValue(txt);
		}
		map.drawingTools.refreshDownloadLinkFromGeoJson.bind(this);
		if (map.mode === 'drawCenterPointMarker') {
			map.drawingTools.area_location = geoJson;
		}
		if (map.mode === 'drawPolygon') {
			map.drawingTools.boundary = geoJson;
		}
	});
};


//Refresh different components from other components.
DrawingTools.prototype.fitMapToGeoJsonFromData = function (e) {
	"use strict";
	//console.log(e);
	var map = initialize_map.map;  //context of this about to change in next call.
	if( typeof map !== 'undefined') {
		if( typeof map.data !== 'undefined') {
			map.data.forEach(function(feature, map){
				fitMapBoundsTofeature(feature);		
			});
		}
	}
};

//Replace the data layer with a new one based on the inputted geoJson.

DrawingTools.prototype.refreshDataFromGeoJson = function () {
	"use strict";
	
	var map = this.map;
	
	var newData = new google.maps.Data({
		map : map,
		style : map.data.getStyle(),
		controls : null,
		drawingMode: null
	});
	var editor = initialize_map.editor;
	if (typeof editor !== 'undefined') {
		var value = editor.getValue();
		try {
			//var userObject = JSON.parse(this.geoJsonInput.value);
			var userObject = JSON.parse(value);
			var newFeatures = newData.addGeoJson(userObject);
		} catch (error) {
			newData.setMap(null);
			if (value !== "") {
				this.setGeoJsonValidity(false, error.message);
				console.log(error.message);
			} else {
				this.setGeoJsonValidity(true, null);
			}
			return;
		}
	}		
	// No error means GeoJSON was valid!
	this.map.data.setMap(null);
	this.map.data = newData;
	this.bindDataLayerListeners();

	this.setGeoJsonValidity(true, null);
};

// Refresh download link.
DrawingTools.prototype.refreshDownloadLinkFromGeoJson = function () {
	"use strict";

	var editor = initialize_map.editor;
	if (typeof editor !== 'undefined') {
		var value = editor.getValue();
		this.downloadLink.download = 'area_' + $('#area_name').val() + ".json";		
		this.downloadLink.href = "data:;base64," + btoa(value);
	}	
};

// Display the validity of geoJson.
DrawingTools.prototype.setGeoJsonValidity = function (newVal, message) {
	"use strict";
	if (!newVal) {
		//this.geoJsonInput.className = 'invalid';
		if (typeof message === undefined){
			message = 'setGeoJsonValidity() no message';
		}
		$('#errors-link').prop('tooltipText', message);
	} 
	else {
		//this.geoJsonInput.className = '';
		this.refreshDownloadLinkFromGeoJson();
	}
};



/**
 * Control the drag and drop panel. Adapted from this code sample:
 * https://developers.google.com/maps/documentation/javascript/examples/layer-data-dragndrop
 * @param e event
 */
function handleDrop(e, map) {
	
	"use strict";
	e.preventDefault();
	e.stopPropagation();
	hideDropPanel(e);

	var files = e.originalEvent.dataTransfer.files;
	console.log('filelen ' + files.length);
	console.log('files ' + files);
	
	if (files.length) {
		// process file(s) being dropped
		// grab the file data from each file
		for (var i = 0, file; file = files[i]; i++) {
			var reader = new FileReader();
			reader.file = file;
			reader.onload = function(e) {
				var filename = this.file.name;
				try {
					console.log('handleDrop() result: ' + e.target.result);
					map.data.addGeoJson(JSON.parse(e.target.result));
				}
				catch(error)  {
					//alert('Error parsing GeoJson in file: ' + filename + ': ' + error);
					console.log('Error parsing GeoJson in file: ' + filename + ': ' + error);
				}
			};
			reader.onerror = function(e) {
				console.error('reading failed');
			};
			reader.readAsText(file);
		}
	} 
	else {
		// process non-file (e.g. text or html) content being dropped
		// grab the plain text version of the data
		var plainText = e.dataTransfer.getData('text/plain');
		if (plainText) {
			map.data.addGeoJson(JSON.parse(plainText));
			//map.data.forEach(function(feature, map_p){
			//	fitMapBoundsTofeature(feature);			
			//});
		}
		else {
			console.log('nothing to drop!');
		}
	}
	// prevent drag event from bubbling further
	return false;
}

/*
 * TODO better to make this a prototype of map.
 * google.maps.event.addListener(map.data,'addfeature',function(e){ 
 * Note: Does not fitBounds when getBounds() is undefined. So map retains mapview when preloaded with geojson.
 */
function fitMapBoundsTofeature(feature) {
	
	"use strict";
	var geometry = feature.getGeometry();
	//var old_bounds = initialize_map.map.getBounds();
	var bounds = initialize_map.map.getBounds();
	if (typeof bounds !== 'undefined') {
		var old_ne = bounds.getNorthEast();
		var old_sw = bounds.getSouthWest();
		
		console.log( 'orig bounds     ' + bounds.toString());
		
		var type = geometry.getType();
		var pt; 
		switch (type) {
			case "Polygon": 
			case "MultiPolygon":
				console.log('Extending map to fit ' + type);
				var polys = geometry.getArray();
				var polycount = polys.length;
				for (var i = 0; i < polycount; i++) {
					var polygon = polys[i];
					var polypoints = polygon.getLength();
					for (pt = 0; pt < polypoints; pt++) {
						var point = polygon.getAt(pt);
						//console.log('extend to point ' + point.toString());
						//if (bounds.contains(point) === false) {
							//console.log('poly point is type' + typeof(point));
							bounds.extend(point);
						//}
					}
				}
				break;
	
			case "Point": 
				console.log('Extending map to fit ' + type);
				pt = geometry.get();
				//console.log('point is type' + typeof(pt));
				bounds.extend(pt);
				break;
	
			case "MultiPoint":
				//console.log('Extending map to fit ' + type);
	            var points = geometry.getArray();
	            for (var mp = 0; mp < points.length; mp++) {
	    			bounds.extend(points[mp]);
	            }
	            break;
	
			default: // "LineString", "MultiLineString", "LinearRing", "GeometryCollection"
				console.log('Extending to geometry of type ' + type + ' not implemented.');
				return;
		}
		/*
		console.log( 'now  bounds     ' + bounds.toString());
		console.log( 'old nw ' + old_ne.toString());
		console.log( 'old sw ' + old_sw.toString());
		*/	
		if(( bounds.getNorthEast().equals(old_ne) === false) || ( bounds.getSouthWest().equals(old_sw) === false )) {
			console.log('fitting Map to new bounds ' + bounds.toString());
			initialize_map.map.fitBounds(bounds);
		}
	}	
}

/**
 * return data layer as JSON string. 
 */

DrawingTools.prototype.getDataValue = function () {
	"use strict";

	var editor = initialize_map.editor;
	if (typeof editor !== 'undefined') {
		var value = editor.getValue();
		this.downloadLink.download = 'area_' + $('#area_name').val() + ".json";		
		this.downloadLink.href = "data:;base64," + btoa(value);
	}	
};


/*
DrawingTools.prototype.resizeGeoJsonInput = function () {
	"use strict";

	var geoJsonInputRect = initialize_map.map.drawingTools.geoJsonInput.getBoundingClientRect();
	var panelRect = initialize_map.map.drawingTools.geoJsonPanel.getBoundingClientRect();
	var height = panelRect.bottom - geoJsonInputRect.top - 4
			+ "px";

	initialize_map.map.drawingTools.geoJsonInput.style.height = height;
};

*/


function geojson_notused_validate(editor, changeObj) { /* not used */
	'use strict';
    var err = geojsonhint.hint(editor.getValue());
    editor.clearGutter('error');

    if (err instanceof Error) {
        handleError(err.message);
        return callback({
            'class': 'icon-circle-blank',
            title: 'invalid JSON',
            message: 'invalid JSON'});
    } else if (err.length) {
        handleErrors(err);
        return callback({
            'class': 'icon-circle-blank',
            title: 'invalid GeoJSON',
            message: 'invalid GeoJSON'});
    } else {
        var zoom = changeObj.from.ch === 0 &&
            changeObj.from.line === 0 &&
            changeObj.origin === 'paste';

        var gj = JSON.parse(editor.getValue());

        try {
            return callback(null, gj, zoom);
        } catch(e) {
            return callback({
                'class': 'icon-circle-blank',
                title: 'invalid GeoJSON',
                message: 'invalid GeoJSON'});
        }
    }

    function handleError(msg) {
        var match = msg.match(/line (\d+)/);
        if (match && match[1]) {
            editor.clearGutter('error');
            editor.setGutterMarker(parseInt(match[1], 10) - 1, 'error', makeMarker(msg));
        }
    }

    /* probably never called */
    function handleErrors(errors) {
        editor.clearGutter('error');
        errors.forEach(function(e) {
            editor.setGutterMarker(e.line, 'error', makeMarker(e.message));
        });
    }

    function makeMarker(msg) {
        return d3.select(document.createElement('div'))
            .attr('class', 'error-marker')
            .attr('message', msg).node();
    }
}
