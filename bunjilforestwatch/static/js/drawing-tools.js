/**
 * @name base=drawing-tools.js
 * @version 1.0
 * @author Chris Goodman
 * @copyright (c) Copyright (c) 2013 Licences: Creative Commons Attribution
 * @fileoverview Displays the google Drawing Manager tool bar on a map with
 *               minor customisations.
 */


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
	// Initialise the map.
	this.mapContainer = mapContainer_p;
	this.dropContainer = dropContainer_p;
	this.geoJsonPanel = geoJsonPanel_p;
	this.geoJsonInput = geoJsonInput_p;
	this.downloadLink = downloadLink_p;
	
	//map_p.data.setControls([ 'Point', 'Polygon' ]);
	
	map_p.data.setStyle({
		editable : true,
		draggable : true
	});
	this.map = map_p;
	this.map.mode = "none";
	this.bindDataLayerListeners();

	var geoJsonInputRect = this.geoJsonInput.getBoundingClientRect();
	var panelRect = this. geoJsonPanel.getBoundingClientRect();
	this.geoJsonInput.style.height = panelRect.bottom - geoJsonInputRect.top - 8
			+ "px";
	
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
			this.refreshDataFromGeoJson);
	google.maps.event.addDomListener(this.geoJsonInput, 'input',
			this.refreshDownloadLinkFromGeoJson);

	// Set up events for styling.
	google.maps.event.addDomListener(window, 'resize', this.resizeGeoJsonInput);
}

//Apply listeners to refresh the GeoJson display on a given data layer.
DrawingTools.prototype.bindDataLayerListeners = function () {
	"use strict";
	this.map.data.addListener('addfeature', this.refreshGeoJsonFromData);
	this.map.data.addListener('addfeature', this.fitMapToGeoJsonFromData);
	this.map.data.addListener('removefeature', this.refreshGeoJsonFromData);
	this.map.data.addListener('setgeometry', this.refreshGeoJsonFromData);
}


/**
 * Create a data layer for points.
 * Give it a function to call when a point is marker is added.
 */
DrawingTools.prototype.drawCenterPointMarker  = function (stop_handler) {
	"use strict";
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
	this.setGeoJsonValidity(true, this.geoJsonInput);
	//this.map.setOptions({
	//		disableDefaultUI: true // no drawing controls
	//});
	this.map.mode = 'drawCenterPointMarker';
	
	this.map.data.addListener('addfeature', stop_handler);
}

DrawingTools.prototype.stopDrawCenterPointMarker=function () {
	"use strict";
	
	this.map.data.setOptions({
		drawingMode: null
	});
	this.map.setOptions({
		disableDefaultUI: false// no drawing controls
	});
	this.map.mode = 'none';
}

DrawingTools.prototype.removeCenterPointMarker=function () {
	"use strict";
	this.map.data.setMap(null);
	this.bindDataLayerListeners();
	this.setGeoJsonValidity(true, this.geoJsonInput);
}



//Refresh different components from other components.
DrawingTools.prototype.refreshGeoJsonFromData = function (e) {
	"use strict";
	//console.log(e);
	var map = this.map;  //context of this about to change in next call.
	map.data.toGeoJson(function(geoJson) {
		map.drawingTools.geoJsonInput.value = JSON.stringify(geoJson, null, 2);
		map.drawingTools.refreshDownloadLinkFromGeoJson();
	});
	
	if (map	.mode === 'drawCenterPointMarker') {
		map.drawingTools.stopDrawCenterPointMarker();
	};
}


//Refresh different components from other components.
DrawingTools.prototype.fitMapToGeoJsonFromData = function (e) {
	"use strict";
	//console.log(e);
	var map = this.map;  //context of this about to change in next call.
	map.data.forEach(function(feature, map_p){
		fitMapBoundsTofeature(feature);			
	});
}

//Replace the data layer with a new one based on the inputted geoJson.
DrawingTools.prototype.refreshDataFromGeoJson = function () {
	"use strict";
	var newData = new google.maps.Data({
		map : this.map,
		style : this.map.data.getStyle(),
		controls : [ 'Point', 'Polygon' ],
		drawingMode: 'Point'
	});
	try {
		var userObject = JSON.parse(this.geoJsonInput.value);
		var newFeatures = newData.addGeoJson(userObject);
	} catch (error) {
		newData.setMap(null);
		if (this.geoJsonInput.value !== "") {
			this.setGeoJsonValidity(false, this.geoJsonInput);
		} else {
			this.setGeoJsonValidity(true, this.geoJsonInput);
		}
		return;
	}
	// No error means GeoJSON was valid!
	this.map.data.setMap(null);
	this.map.data = newData;
	this.bindDataLayerListeners();

	this.setGeoJsonValidity(true, this.geoJsonInput);

}

// Refresh download link.
DrawingTools.prototype.refreshDownloadLinkFromGeoJson = function () {
	"use strict";
	this.downloadLink.href = "data:;base64," + btoa(this.geoJsonInput.value);
}



// Display the validity of geoJson.
DrawingTools.prototype.setGeoJsonValidity = function (newVal) {
	"use strict";
	if (!newVal) {
		this.geoJsonInput.className = 'invalid';
	} else {
		this.geoJsonInput.className = '';
	}
}



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
					console.log('result' + e.target.result);
					map.data.addGeoJson(JSON.parse(e.target.result));
				}
				catch(error)  {
					alert('Error parsing GeoJson in file: ' + filename + ': ' + error);
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
			console.log('nothing to drop!')
		}
	}
	// prevent drag event from bubbling further
	return false;
}

/*
 * TODO better to make this a prototype of map.
 * google.maps.event.addListener(map.data,'addfeature',function(e){ 
 */
function fitMapBoundsTofeature(feature) {
	
	"use strict";
	var geometry = feature.getGeometry();
	//var old_bounds = initialize_map.map.getBounds();
	var bounds = initialize_map.map.getBounds();
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
					var point = polygon.getAt(pt)
					//console.log('extend to point ' + point.toString());
					//if (bounds.contains(point) === false) {
						console.log('poly point is type' + typeof(point));
						bounds.extend(point);
					//}
				}
			}
			break;

		case "Point": 
			console.log('Extending map to fit ' + type);
			pt = geometry.get();
			console.log('point is type' + typeof(pt));
			bounds.extend(pt);
			break;

		case "MultiPoint":
			console.log('Extending map to fit ' + type);
            var points = geometry.getArray();
            for (var mp = 0; mp < points.length; mp++) {
    			bounds.extend(points[mp]);
            }
            break;

		default: // "LineString", "MultiLineString", "LinearRing", "GeometryCollection"
			console.log('Extending to geometry of type ' + type + ' not implemented.');
			return;
	}
	console.log( 'now  bounds     ' + bounds.toString());
	console.log( 'old nw ' + old_ne.toString());
	console.log( 'old sw ' + old_sw.toString());
	
	if(( bounds.getNorthEast().equals(old_ne) === false) || ( bounds.getSouthWest().equals(old_sw) === false )) {
		console.log('fitting Map to new bounds ' + bounds.toString());
		initialize_map.map.fitBounds(bounds);
	}
}


/*
//Styling related functions.
DrawingTools.prototype.resizeGeoJsonInput = function () {
	"use strict";
	var geoJsonInputRect = this.map.drawingTools.geoJsonInput.getBoundingClientRect();
	var panelRect = this.geoJsonPanel.getBoundingClientRect();
	this.geoJsonInput.style.height = panelRect.bottom - geoJsonInputRect.top - 8
			+ "px";
}
*/
