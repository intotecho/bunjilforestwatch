/*******************************************************************************
 * Copyright (c) 2014 Chris Goodman GPLv2 Creative Commons License to share
 * See also https://developers.google.com/maps/documentation/javascript/examples/overlay-hideshow
 ******************************************************************************/
//var landsat_overlays = []; //empty array of cell overlays. TODO move to this.

var LANDSAT_GRID_FT = '1kSWksPYW7NM6QsC_wnCuuXO7giU-5ycxJb2EUt8';// https://www.google.com/fusiontables/DataSource?docid=1kSWksPYW7NM6QsC_wnCuuXO7giU-5ycxJb2EUt8
var COUNTRY_GRID_FT = '1foc3xO9DyfSIF6ofvN0kp2bxSfSeKog5FbdWdQ'; // https://www.google.com/fusiontables/data?docid=1foc3xO9DyfSIF6ofvN0kp2bxSfSeKog5FbdWdQ
var MAPS_API_KEY = 'AIzaSyDxcijg13r2SNlryEcmi_XXxZ9sO4rpr8I';    // #Google Maps API public key


var landsatgrid_panel = '#map_panel'; // panel used to display info about the selected cell. Client may set this.



/* LandsatGridOverlay(map, opacity, clickable, cellarray)
 * 
 * clickable;  For /new-area, we want it to be visible but non-interactive. 
 *			   For /view-area, we want to be able to click on grid cells.
 */
function LandsatGridOverlay(map, opacity, clickable, cellarray) {
  // Call the parent constructor, making sure (using Function#call) that "this" is
  // set correctly during the call
  this.map = map;
  this.cellarray = cellarray;
  this.opacity = opacity;
  this.clickable = clickable;

  this.visible = false;
  this.initialized = false;
  this.landsat_overlays = []; //empty array of cell overlays.
  this.selectedPath = -1;
  this.selectedRow = -1;
	  
  google.maps.OverlayView.call(this);
}

//Create a LandsatGridOverlay.prototype object that inherits from Overlay.prototype.
//LandsatGridOverlay.prototype = Overlay.create(LandsatGridOverlay.prototype); // See note below

LandsatGridOverlay.prototype = new google.maps.OverlayView();

//Set the "constructor" property to refer to Overlay
LandsatGridOverlay.prototype.constructor = google.maps.OverlayView;

LandsatGridOverlay.prototype.initialize = function () {
    console.log( "LandsatGridOverlay() initialising");
	if (this.initialized) {
		return;
	}
	var self = this.self;
	
	if (this.map === undefined){
		console.log('requestLandsatGrid() map is undefined');
		return;
	}
	//this.map.overlayMapTypes.insertAt(0, self);  //what's this for?
		
	var url;
	//if server sent a cellarray use that to query fusion table.
	//else query a radius around the current map bounds.
	if (this.cellarray == null) {
		url = queryLandsatFusionTableRadius(this.map);
	} else {
		url = queryLandsatFusionTableCellArray(this.map, cellarray);
	}
	var tmpLandsatGridOverlay = this;
	
	$.ajax({
         url: url.join(''),
         dataType: 'jsonp',
         success: function (data) {
        	createLandsatGrid(data, tmpLandsatGridOverlay);
         },
         error: function (jqxhr, textStatus, error) { 
        	var err = textStatus + ', ' + error;
     	    console.log( "LandsatGridOverlay() initialise Failed: " + err);
         }
	});
}

LandsatGridOverlay.prototype.hide = function () {
	this.visible = false;
	//make each cell hidden
	for (var i = 0; i < this.landsat_overlays.length; i++ ) {
		this.landsat_overlays[i].setVisible(false)
	}
}

LandsatGridOverlay.prototype.show = function () {
	//this.initialize();
	this.visible = true;
	//make each cell visible
	for (var i = 0; i < this.landsat_overlays.length; i++ ) {
		this.landsat_overlays[i].setVisible(true)
	}
}

/*
 * op from 0 (totally transparent so invisible) to 100 (non transparent).
 */
LandsatGridOverlay.prototype.setOpacity = function (op) {
	console.log("LandsatGridOverlay::setOpacity(): " + op);
	this.opacity = op;
	//set opacity of each cell 
	for (var i = 0; i < this.landsat_overlays.length; i++ ) {	
		this.landsat_overlays[i].setOptions(
			{
			  strokeOpacity : op / 100,
			  fillOpacity : 0 // clear unless mouseover.
			});
		this.landsat_overlays[i].setVisible(true);
	}
	google.maps.event.trigger(this.map,'resize');
}
	
// return the cells within a RADIUS of the map center.
function queryLandsatFusionTableRadius(map) {
	
	var map_center = map.getCenter();

	var map_distance = google.maps.geometry.spherical.computeDistanceBetween(
			map.getBounds().getNorthEast(), 
			map.getBounds().getSouthWest());
	var radius = 280000; // how far away to show cells from a small AOI in
							// metres
	var distance = (map_distance > radius) ? map_distance : radius; // The view
																	// area
	distance = (distance > radius) ? radius : distance; // unless the view area
														// is more than 2000km.
	distance = (distance > 2800000) ? 2800000 : distance; // clip the view
															// area to 2000km.

	console.log(radius, map_distance, distance);

	// script = document.createElement('script');
	var url = [ 'https://www.googleapis.com/fusiontables/v1/query?' ];
	url.push('sql=');
	var query = 'SELECT name, geometry, description FROM ' + LANDSAT_GRID_FT
			+ ' WHERE ST_INTERSECTS(geometry, CIRCLE(LATLNG' + map_center
			+ ' , ' + distance + ' ))';
	console.log("ft query: ", query);
	var encodedQuery = encodeURIComponent(query);
	url.push(encodedQuery);
	url.push('&callback=?');
	url.push('&key=' + MAPS_API_KEY);
	return url;
}

// return cells that overlap the RECTANGLE or AOI bounds - not used.
function queryLandsatFusionTableBounds(map, latlngbounds) {
	var url = [ 'https://www.googleapis.com/fusiontables/v1/query?' ];
	url.push('sql=');

	var query = 'SELECT name, geometry, description FROM ' + LANDSAT_GRID_FT
			+ ' WHERE ST_INTERSECTS(geometry, RECTANGLE(LATLNG('
			+ latlngbounds.min_lat + ', ' + latlngbounds.min_lon + '),LATLNG('
			+ latlngbounds.max_lat + ', ' + latlngbounds.max_lon + ')))';

	console.log("ft query: ", query);
	var encodedQuery = encodeURIComponent(query);
	url.push(encodedQuery);
	url.push('&callback=?');
	url.push('&key=' + MAPS_API_KEY);
	return url;
}

function queryLandsatFusionTableCellArray(map, cellarray) {
	
	var url = [ 'https://www.googleapis.com/fusiontables/v1/query?' ];
	url.push('sql=');

	var cellnames = []; // Construct a query of FT WHERE name IN cellnames

	for (var i = 0; i < cellarray.length; i++) {
		cellnames.push("'" + cellarray[i].path + '_' + cellarray[i].row + "' ");
	};

	var query = 'SELECT name, geometry, description FROM ' + LANDSAT_GRID_FT
			+ " WHERE name IN (" + cellnames + ")";

	var encodedQuery = encodeURIComponent(query);
	url.push(encodedQuery);
	url.push('&callback=?');	
	url.push('&key=' + MAPS_API_KEY);
	console.log("ft query: " + query + " ft url: " + url);
	return url;
}


//This is the callback that creates the Landsat Grid.
function createLandsatGrid(data, landsatGridOverlay) {
    
	"use strict";
	//current_map = map; //TODO how to get parameters.
	
	var rows = data.rows;
	for ( var i in rows) {

		// console.log(data);
		var newCoordinates = [];
		var geometry = rows[i][1].geometry;

		if (geometry) {
			newCoordinates = polygon2LatLngCoordinates(geometry);
			var description = rows[i][2];

			// converts the YAML html description to JS object.
			var cellobject = YAML.parse(description); 

			var selectedPath = parseInt(cellobject['<strong>PATH</strong>'], 10);
			var selectedRow = parseInt(cellobject['<strong>ROW</strong>'], 10);

			// colour as checkerboard
			// checkerboard = (both are odd) or (both are even).
			var cell_colour;

			if ((selectedPath % 2) == (selectedRow % 2)) {
				cell_colour = '#F0FFFF';
			} 
			else {
				cell_colour = '#FFF0FF';
			}

			var landsat_cell = new google.maps.Polygon({
				paths : newCoordinates,
				strokeColor : cell_colour,
				strokeWeight : 1,
				strokeOpacity : 1,
				fillOpacity : 0,
				editable : false,
				clickable : landsatGridOverlay.clickable,
				suppressInfoWindows : true,
				goedesic : true,
				// pointer-events: none,
				content : description
			});
			
			// add non standard new attributes
			landsat_cell['path']   = selectedPath;
			landsat_cell['row']    = selectedRow;
			landsat_cell['parent'] = landsatGridOverlay;
			
			
			if (isMonitored(selectedPath, selectedRow, landsatGridOverlay.cellarray) == "true") {		
				//landsat_cell.set('Monitored', true);
				monitor_cell(landsat_cell, true);
				
			} else {
				//landsat_cell.set('Monitored', false);
				monitor_cell(landsat_cell, false);
			}

			landsat_cell.set("Description", description); 
			// Add attribute description in polygon.

			landsatGridOverlay.landsat_overlays.push(landsat_cell);

			google.maps.event.addListener(landsat_cell, 'click',
					landsatGrid_click);
			google.maps.event.addListener(landsat_cell, 'mouseover',
					landsatGrid_mouseover);
			google.maps.event.addListener(landsat_cell, 'mouseout',
					landsatGrid_mouseout);
			google.maps.event.addListener(landsat_cell, 'zoom',
					landsatGrid_zoom);
			
			landsat_cell.setMap(landsatGridOverlay.map);
		
			$(landsatgrid_panel).collapse('show');
		} // if geometry
		else {
			console.log("no geometry ", i);
		}
	} // each row of cell data
	landsatGridOverlay.initialized = true;
}

/*
 * polygon2LatLngCoordinates() creates an array of GoogleLatLngs from a Polygon.
 */
function polygon2LatLngCoordinates(polygon) {
	"use strict";
	var newCoordinates = [];
	var coordinates = polygon['coordinates'][0];
	for ( var i in coordinates) {
		newCoordinates.push(new google.maps.LatLng(coordinates[i][1],
				coordinates[i][0]));
	}
	return newCoordinates;
}


//Used in initial drawing of grid 
function isMonitored(selectedPath, selectedRow, cellarray) {
	if (cellarray != null) {
		for (var i = 0; i < cellarray.length; i++) {
			if ((cellarray[i].path == selectedPath)
					&& (cellarray[i].row == selectedRow)) {
				return cellarray[i].monitored;
			}
		}
		console.log("isMonitored(): missing cell %d, %d", selectedPath,
				selectedRow);
	}
	return false;
}

//monitor_cell() returns true if the cell overlay has isMonitored set.
function monitor_cell(landsat_cell, isMonitored) {
	
	landsat_cell.Monitored = isMonitored;
		
	if (isMonitored == true) {
		landsat_cell.setOptions({
			strokeWeight : 4
		
		})
	} else {
		landsat_cell.setOptions({
			strokeWeight : 0.5
		})
		//console.log("createLandsatGrid() unmonitored cell");
	}
	return isMonitored;
}

function landsatGrid_mouseover(e) {

	if (this.Monitored) {
		this.setOptions({
			fillOpacity : 0.3 * this.parent.opacity / 100
		})
	} else {
		this.setOptions({
			fillOpacity : 0.1 * this.parent.opacity / 100
		})
	}
	display_cell_info(this, false)
}

function landsatGrid_mouseout(e) {
	this.setOptions({
		fillOpacity : 0
	})
	$(landsatgrid_panel).empty();
}

function landsatGrid_click(e) {
	display_cell_info(this, true)
	this.parent.selectedPath = this.path;
	this.parent.selectedRow = this.row;
	
	cellSelected(this);
}

/*
function hideLandsatGrid() {
	"use strict";
	for (var i = 0; i <landsat_overlays.length;i++ ) {
		landsat_overlays[i].setVisible(false)
	}
}

function showLandsatGrid() {
	"use strict";
	for (var i = 0; i <landsat_overlays.length;i++ ) {
		landsat_overlays[i].setVisible(true)
	}
}

function removeLandsatGrid() {
	"use strict";

	while (landsat_overlays.length > 0) {
		var landsat_cell = landsat_overlays.pop();
		landsat_cell.setVisible(false);
		landsat_cell.setMap(null);
	}
}

function setOpacityLandsatGrid() {
	"use strict";

	while (landsat_overlays.length > 0) {
		var landsat_cell = landsat_overlays.pop();
		landsat_cell.setVisible(false);
		landsat_cell.setMap(null);
	}
}


LandsatGridOverlay.prototype.setCellOpacity = function (obj) {
	alert('not implemented')
	console.log("object style: %s, %s, %s, %s.", obj.style.filter, obj.style.KHTMLOpacity, obj.style.MozOpacity, obj.style.opacity );
	if (this.opacity > 0) {
		if (typeof (obj.style.filter) == 'string') { obj.style.filter = 'alpha(opacity:' + this.opacity + ')'; }
		if (typeof (obj.style.KHTMLOpacity) == 'string') { obj.style.KHTMLOpacity = this.opacity / 100; }
		if (typeof (obj.style.MozOpacity) == 'string') { obj.style.MozOpacity = this.opacity / 100; }
		if (typeof (obj.style.opacity) == 'string') { obj.style.opacity = this.opacity / 100; }
	}
}

*/

function landsatGrid_zoom(e) {
	// needs work
	if (e.zoom() < 6) {
		landsat_cell.hidden();
	} else {
		landsat_cell.show();
	}
	console.log(e.zoom());
}

function display_cell_info(e, isSelected) {
	// console.log('display_cell_info()')
	cellobject = YAML.parse(e.get("Description")); // converts the YAML html
													// description to JS object.
	var path = parseInt(cellobject['<strong>PATH</strong>'], 10);
	var row = parseInt(cellobject['<strong>ROW</strong>'], 10);
	//or path = e.path;
	
	if (isSelected = true) {
		var selectedPath = path;
		var selectedRow = row;
		e.selectedLAT_UL = parseFloat(cellobject['<strong>LAT UL</strong>']);
		e.selectedLON_UL = parseFloat(cellobject['<strong>LON UL</strong>']);
		e.selectedLAT_UR = parseFloat(cellobject['<strong>LAT UR</strong>']);
		e.selectedLON_UR = parseFloat(cellobject['<strong>LON UR</strong>']);
		e.selectedLAT_LL = parseFloat(cellobject['<strong>LAT LL</strong>']);
		e.selectedLON_LL = parseFloat(cellobject['<strong>LON LL</strong>']);
		e.selectedLAT_LR = parseFloat(cellobject['<strong>LAT LR</strong>']);
		e.selectedLON_LR = parseFloat(cellobject['<strong>LON LR</strong>']);
	}

	$(landsatgrid_panel).empty();
	htmlString = "<p><font-size:50%;color:blue strong>zoom:</strong> "
	//		+ map.getZoom() + "</p>"
	//      + "<p>lat: " + map.getCenter().lat().toFixed(3) + ", lng: "
	//		+ map.getCenter().lng().toFixed(3) + "<br>" 
			+ "Path: " + parseInt(e.path, 10) 
			+ " Row: " + parseInt(e.row, 10);
	if (e.get("Monitored") == true) {
		htmlString += " Monitored"
	} else {
		htmlString += " Unmonitored"
	}
	htmlString += "<br></p>";
	$(landsatgrid_panel).html(htmlString);
}




