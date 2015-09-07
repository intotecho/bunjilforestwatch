/**
 * @name landsat-grid.js
 * @version 1.0
 * @author Chris Goodman 
 * @copyright (c) 2014 Chris Goodman GPLv2 Creative Commons License to share
 * @fileoverview Display the outlines of landsat swathes in a grid on the map.
 *  * See also https://developers.google.com/maps/documentation/javascript/examples/overlay-hideshow
 */

/**
 * @global 
 * @summary {@link https://www.google.com/fusiontables/DataSource?docid=1kSWksPYW7NM6QsC_wnCuuXO7giU-5ycxJb2EUt8}
 */
var LANDSAT_GRID_FT = '1kSWksPYW7NM6QsC_wnCuuXO7giU-5ycxJb2EUt8';
/**
 * @global 
 * @summary {@link https://www.google.com/fusiontables/data?docid=1foc3xO9DyfSIF6ofvN0kp2bxSfSeKog5FbdWdQ }
 */
var COUNTRY_GRID_FT = '1foc3xO9DyfSIF6ofvN0kp2bxSfSeKog5FbdWdQ'; 
/**
 * @global 
 * @summary Google Maps API public key
 */
var MAPS_API_KEY = 'AIzaSyDxcijg13r2SNlryEcmi_XXxZ9sO4rpr8I';

/**
 * @global 
 * @summary panel used to display info about the selected cell. Client may set this.
 */

var landsatgrid_panel = '#cell_panel';

/**
 * @global 
 */
var edit_cells_mode = true; // toggled by initialise to false.

/** 
 * @decr   Call the parent constructor, making sure (using Function#call) that "this" is
  set correctly during the call
 * @param {Googlemap } map 
 * @param {Number} opacity
 * @param {Boolean} clickable;  Is the overlay clickable? 
 * For /new-area, we want it to be visible but non-interactive. 
 *			   For /view-area, we want to be able to click on grid cells.
 * @param  cellarray an array of cells containing the geometry of the cells.
 * 
 */

function LandsatGridOverlay(map, opacity, clickable, cellarray) {
  "use strict"
  this.map = map;
  this.cellarray = cellarray;
  this.opacity = opacity;
  this.clickable = clickable;

  this.visible = false;
  this.initialized = false;
  this.landsat_overlays = []; //empty array of cell overlays.
  this.selectedPath = -1;
  this.selectedRow = -1;
  this.hoverPath = -1;
  this.hoverRow = -1;
    
  google.maps.OverlayView.call(this);
}



/** Create a LandsatGridOverlay.prototype object that inherits from Overlay.prototype.
 * @global   
 */
LandsatGridOverlay.prototype = new google.maps.OverlayView();

/** 
 * Set the "constructor" property to refer to Overlay
 * @global   
 */

LandsatGridOverlay.prototype.constructor = google.maps.OverlayView;

/** @decr   Create a LandsatGridOverlay.prototype object that inherits from Overlay.prototype.
 * LandsatGridOverlay.prototype = Overlay.create(LandsatGridOverlay.prototype); // See note below
 * LandsatGridOverlay(map, opacity, clickable, cellarray)
 * 
 */

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
	if (this.cellarray === null) {
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

/** hide a LandsatGridOverlay
 * 
 */
LandsatGridOverlay.prototype.hide = function () {
	this.visible = false;
	//make each cell hidden
	for (var i = 0; i < this.landsat_overlays.length; i++ ) {
		this.landsat_overlays[i].setVisible(false)
	}
}

/** show a LandsatGridOverlay
 * 
 */
LandsatGridOverlay.prototype.show = function () {
	//this.initialize();
	this.visible = true;
	//make each cell visible
	for (var i = 0; i < this.landsat_overlays.length; i++ ) {
		this.landsat_overlays[i].setVisible(true)
	}
}

/** setOpacity 
 * op from 0 (totally transparent so invisible) to 100 (non transparent or opaque).
 */
LandsatGridOverlay.prototype.setOpacity = function (op) {
	console.log("LandsatGridOverlay::setOpacity(): " + op);
	this.opacity = op;
	//set opacity of each cell 
	for (var i = 0; i < this.landsat_overlays.length; i++ ) {	
		this.landsat_overlays[i].setOptions(
			{
			  strokeOpacity : op,
			  fillOpacity : 0 // clear unless mouseover.
			});
		this.landsat_overlays[i].setVisible(true);
	}
	google.maps.event.trigger(this.map,'resize');
}
	

/** 
 * @returns the cells within a RADIUS of the map center.
 */
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


/**
 * @param map
 * @param latlngbounds 
 * @returns cells that overlap the RECTANGLE or AOI bounds - not used.
 * 
 */
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


/**
 * @descr Filter the global landsat grid to just the matching cells passed in cellarray.
 * @param map
 * @param cellarray
 * @returns url
 * 
 */

function queryLandsatFusionTableCellArray(map, cellarray) {
	
	var url = [ 'https://www.googleapis.com/fusiontables/v1/query?' ];
	url.push('sql=');

	var cellnames = []; // Construct a query of FT WHERE name IN cellnames

	if (cellarray !== null) {
		for (var i = 0; i < cellarray.length; i++) {
			cellnames.push("'" + cellarray[i].path + '_' + cellarray[i].row + "' ");
		};
	}
	var query = 'SELECT name, geometry, description FROM ' + LANDSAT_GRID_FT
			+ " WHERE name IN (" + cellnames + ")";

	var encodedQuery = encodeURIComponent(query);
	url.push(encodedQuery);
	url.push('&callback=?');	
	url.push('&key=' + MAPS_API_KEY);
	console.log("ft query: " + query + " ft url: " + url);
	return url;
}



/**
 * This is the callback that creates the Landsat Grid and draws it on the map.
 * @param data
 * @param landsatGridOverlay
 * 
 */
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

			// colour as checkerboard (both are odd) or (both are even).
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
				strokeOpacity : landsatGridOverlay.opacity,
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
				monitor_cell(landsat_cell, true);		
			} else {
				monitor_cell(landsat_cell, false);
			}

			landsat_cell.set("Description", description); 

			landsatGridOverlay.landsat_overlays.push(landsat_cell);

			google.maps.event.addListener(landsat_cell, 'click',
					landsatGrid_click);
			google.maps.event.addListener(landsat_cell, 'mouseover',
					landsatGrid_mouseover);
			google.maps.event.addListener(landsat_cell, 'mouseout',
					landsatGrid_mouseout);
			google.maps.event.addListener(landsat_cell, 'zoom',
					landsatGrid_zoom);
			
			google.maps.event.addListener(landsat_cell, 'mousemove', function (event) {
			        update_map_cursor(landsat_cell, event.latLng, '#map_panel_cursor');               
			});

			landsat_cell.setMap(landsatGridOverlay.map);
		
		} // if geometry
		else {
			console.log("no geometry ", i);
		}
	} // each row of cell data
	landsatGridOverlay.initialized = true;
}

/**
 * @descr polygon2LatLngCoordinates() creates an array of GoogleLatLngs from a Polygon.
 * @param polygon
 * @returns newCoordinates a geojson array
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



//Get Landsat_cell
/**
 * @descr getCellArrrayCell() returns the selected cell json object from cellarray.
 * @param selectedPath
 * @param selectedRow
 * @param cellarray 
 * @returns a cell 
 */

function getCellArrrayCell(selectedPath, selectedRow, cellarray) {
	if (cellarray != null) {
		for (var i = 0; i < cellarray.length; i++) {
			if ((cellarray[i].path == selectedPath)
					&& (cellarray[i].row == selectedRow)) {
				return cellarray[i];
			}
		}
		console.log("getLansatCell(): missing cell %d, %d", 
								selectedPath, selectedRow);
	}
	return null;
}

/**
 * isMonitored returns true if the cell is monitored.
 * @param selectedPath
 * @param selectedRow
 * @param cellarray
 * @returns bool
 */

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


/**
 * @descr monitor_cell() changes the cell style and sets state to monitored according to the isMonitored parameter.
 * @param landsat_cell
 * @param {bool} isMonitored
 * @returns {bool} isMonitored
 */

function monitor_cell(landsat_cell, isMonitored) {
	
	landsat_cell.Monitored = isMonitored;
		
	if (isMonitored == true) {
		landsat_cell.setOptions({
			strokeWeight : 4
		
		});
	} 
	else {
		landsat_cell.setOptions({
			strokeWeight : 0.5
		})
	}
	return isMonitored;
}

/*
 * event handler increases opacity when mouse is over cell.
 */
function landsatGrid_mouseover(e) {

	if (this.Monitored) {
		this.setOptions({
			fillOpacity : 0.3 * this.parent.opacity
		})
	} 
	else {
		this.setOptions({
			fillOpacity : 0.1 * this.parent.opacity 
		})
	}
	this.parent.hoverPath = this.path;
	this.parent.hoverRow = this.row;	
	
	update_cell_panel(this.parent);
}

/*
 * event handler decreases opacity when mouse is over cell.
 */

function landsatGrid_mouseout(e) {
	this.setOptions({
		fillOpacity : 0
	})
	this.parent.hoverPath = -1;
	this.parent.hoverRow = -1;	
	
	update_cell_panel(this.parent);
}

/**
 * Event handler remembers the last clicked cell and call cellSelected()
 * behaviour of {@link cellSelected()} will depend on user context. Eg are cells locked for editing.
 * @param e
 */
function landsatGrid_click(e) {
	
	this.parent.selectedPath = this.path;
	this.parent.selectedRow = this.row;	
	cellSelected(this);
}

/**
 * Event handler is called when zooming in on the overlay.
 * The grid is hidden if zoomed to far out.
 * @param e
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

/**
 * Fetch Outline and status of this Landsat Cell
 * Calls /selectcell/ to get the status
 * @todo: Check it works for special chars in area name.
 * @param landsat_cell - the selected cell.
 */
function cellSelected(landsat_cell)
{

  var cell = getCellArrrayCell(landsat_cell.path, landsat_cell.row, cellarray);
  var div_id = '#cell-panel-' + cell.index;
  var httpget_url = "/selectcell/" + area_json['properties']['area_name'] + "/" + jsonStringifySelectedCell(landsat_cell)
  
  console.log( "cellSelected() %d %d %s %s %s", landsat_cell.path, landsat_cell.row, div_id, (edit_cells_mode == true)?"editing cells":"locked", httpget_url);
  
  //var panel = $("#cell_panel");
  var panel = $(div_id);
  if (panel === null)
  {
	  console.log("error in DOM. missing Cell panel.")
	  return;
  }
  //panel.collapse('show').css('overflow', 'scroll');
  //panel.empty();
  
  if (edit_cells_mode == false) {
	  update_cell_panel(landsat_cell.parent);
	  return;
  }
  
  panel.addClass('cell-panel-updating'); 
  panel.append("Updating Cell...");
  panel.append('<img src="/static/img/ajax-loader.gif" class="ajax-loader"/>');
  $.get(httpget_url).done(function(data) {
	  	  // store toggled cell.
	  	  var celldict = jQuery.parseJSON(data);
		  console.log(celldict);
		  if (celldict['result'] == "ok") { 
			  var cell = getCellArrrayCell(celldict.path, celldict.row, cellarray);
			  if (cell !== null) {
				  cell['LC8_latest_capture'] = celldict.LC8_latest_capture;
				  cell.monitored  = celldict.monitored;
				  if (celldict.monitored == "true") {
					  monitor_cell(landsat_cell, true);
				  }
				  else {
					  monitor_cell(landsat_cell, false);
				  }
			  }
			  else {
				  console.log('cell not found!');
			  }
		      if (celldict.monitored == "true") {
			            console.log( "Now Monitoring: " + celldict.path  + ", " +  celldict.row)
		      }
		      else {
			            console.log( "Stopped Monitoring: " + celldict.path  +", " +  celldict.row)
		      }
		      update_cell_panel(landsat_cell.parent);
		  }
		  else {
		      console.log( "Error: " + celldict['result']);
		  }             
  }).error(function( jqxhr, textStatus, error ) {
		  var err = textStatus + ', ' + error;
		  console.log( "Request Failed: " + err);
		  panel.empty();
		  panel.append("<p>Failed: " + err + "</p>"); 
  });
}

/**
 * 
 * @param landsatGridOverlay
 */
function update_cell_panel(landsatGridOverlay) {

	var panel = $(landsatgrid_panel);
	panel.addClass('cell-panel'); 
	panel.empty();

	var panel_str = ""	
	monitored_cells_count= 0;
	
	var cellarray = landsatGridOverlay.cellarray;
	if (cellarray != null) {
		for (var i = 0; i < cellarray.length; i++) {
	
			var path = cellarray[i].path
            var row  = cellarray[i].row;
			var monitored = cellarray[i].monitored;
			var hover = ((path == landsatGridOverlay.hoverPath)
					&& (row == landsatGridOverlay.hoverRow));
			var selected = ((path == landsatGridOverlay.selectedPath)
					&& (row == landsatGridOverlay.selectedRow));
			
			panel_str += "<div id=cell-panel-" + i + " class=";
			
			if (selected) {
					panel_str += "'cell-panel-selected '";
			}
			else
				panel_str += "'cell-panel-unselected '";
				
			if (hover) { //draw the Cell(n,n) in hover style.
				panel_str += "><span class='cell-panel-hover' data-toggle='tooltip' title='Landsat Cell (Path, Row)'>Cell(";	
			}
			else {
				panel_str += "><span class='cell-panel-nohover' data-toggle='tooltip' title='Landsat Cell (Path, Row)' >Cell(";
			}
			
			panel_str += path  + ", " +  row + ") </span>";  //end of hover div
			   
    		if (monitored == "true") {
    			panel_str += "<span class='cell-panel-monitored data-toggle='tooltip' title='Regular observation tasks will be sent for this cell'> Monitoring </span>";
    			monitored_cells_count += 1;
    		}
    		else
    			panel_str += "<span class='cell-panel-unmonitored' data-toggle='tooltip' title='No observation tasks will be created from this cell'> Unmonitored </span>";
    		
            if (cellarray[i].LC8_latest_capture !== "none") {
            	var datestr =  cellarray[i].LC8_latest_capture.substr(0,  cellarray[i].LC8_latest_capture.indexOf('@')); 
            	panel_str += "<span class='cell-panel-date' data-toggle='tooltip' title='Most Recent Image mm-dd'><a href='#'> " + datestr.substring(5) + "</a>"; //remove initial '2015-'
            }
			panel_str += "<br></div>"; // end-row
		}
		if (monitored_cells_count == 0) {
			panel_str += "<div class='cell-panel-warn'>You won't receive any notifications as no cells monitored!</div>" 
			panel.parent().collapse('show');
		}
	}
	else 	{
		panel_str += "<div class='cell-panel-warn'>Error: No Cells !</div>";
		panel.parent().collapse('show');	
	}		
	panel.html(panel_str);
}


