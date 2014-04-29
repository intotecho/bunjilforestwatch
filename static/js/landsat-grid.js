/*******************************************************************************
 * Copyright (c) 2014 Chris Goodman Creative Commons License to share
 ******************************************************************************/


var LANDSAT_GRID_FT = '1kSWksPYW7NM6QsC_wnCuuXO7giU-5ycxJb2EUt8';// https://www.google.com/fusiontables/DataSource?docid=1kSWksPYW7NM6QsC_wnCuuXO7giU-5ycxJb2EUt8
var COUNTRY_GRID_FT = '1foc3xO9DyfSIF6ofvN0kp2bxSfSeKog5FbdWdQ'; // https://www.google.com/fusiontables/data?docid=1foc3xO9DyfSIF6ofvN0kp2bxSfSeKog5FbdWdQ
var MAPS_API_KEY = 'AIzaSyDxcijg13r2SNlryEcmi_XXxZ9sO4rpr8I'; // https://code.google.com/apis/console/ #Google Maps API public key
var landsat_overlays = [];
var landsatgrid_panel = '#map_panel';
var landsatgrid_isclickable;
var gridInitialised;

var selectedPath = -1 //global - PATH selected by mouse click
var selectedRow  = -1 //global - ROW selected by mouse click

var selectedLAT_UL; //coordinates of the selected Landsat Cell.
var selectedLON_UL;
var selectedLAT_UR; 
var selectedLON_UR;
var selectedLAT_LL;
var selectedLON_LL;
var selectedLAT_LR;
var selectedLON_LR;

var infoWindowArray = [];

function resetInfoWindow() {
    "use strict";
    var i;
    if (infoWindowArray) {
        for (i = 0; i < infoWindowArray.length; i = i + 1) {
            infoWindowArray[i].close();
        }
    }
}

//return the cells within a RADIUS of the map center.
function queryLandsatFusionTableRadius(map) {
	var map_center = map.getCenter(); // new
	// google.maps.LatLng({{area.map_center}});
	var map_distance = google.maps.geometry.spherical
	.computeDistanceBetween(map.getBounds().getNorthEast(), map.getBounds().getSouthWest());
	var radius = 180000; // how far away to show cells from a small AOI in metres
	var distance = (map_distance > radius) ? map_distance : radius; // The	view area
	distance = (distance > radius) ? radius : distance; // unless the view area is more than 2000km.
	distance = (distance > 2500000) ? 2500000 : distance; // clip the view area to 2000km.

	console.log(radius, map_distance, distance);

	//script = document.createElement('script');
	var url = [ 'https://www.googleapis.com/fusiontables/v1/query?' ];
	url.push('sql=');
	var query = 'SELECT name, geometry, description FROM ' +
	LANDSAT_GRID_FT + 
	' WHERE ST_INTERSECTS(geometry, CIRCLE(LATLNG' + 
	map_center + ' , ' + distance + ' ))';
	console.log("ft query: ", query);
	var encodedQuery = encodeURIComponent(query);
	url.push(encodedQuery);
	url.push('&callback=drawLandsatGrid');
	url.push('&key=' + MAPS_API_KEY);
	return url;
}

//return the cells that overlap the RECTANGLE or AOI bounds.
function queryLandsatFusionTableCells(map, latlngbounds) {
	var url = [ 'https://www.googleapis.com/fusiontables/v1/query?' ];
	url.push('sql=');

	var query = 'SELECT name, geometry, description FROM ' +
	LANDSAT_GRID_FT + 
	' WHERE ST_INTERSECTS(geometry, RECTANGLE(LATLNG(' + latlngbounds.min_lat + ', ' + latlngbounds.min_lon +'),LATLNG(' + latlngbounds.max_lat + ', ' + latlngbounds.max_lon +')))';
	
	console.log("ft query: ", query);
	var encodedQuery = encodeURIComponent(query);
	url.push(encodedQuery);
	url.push('&callback=drawLandsatGrid');
	url.push('&key=' + MAPS_API_KEY);
	return url;
}

function requestLandsatGrid(map, showlayer, clickable, cellrange) {
    "use strict";
    // Initialize JSONP request for LANSAT grid Fusion Table
    //   Based on
    //   https://developers.google.com/fusiontables/docs/samples/mouseover_map_styles
    // landsat grid initially published by USGS.
    landsatgrid_isclickable = clickable;
    var script = null;
    if (gridInitialised !== true) {
        if (showlayer === true) {
            gridInitialised = true;
            var url = null;
            if (cellrange == null)
            {
            	url = queryLandsatFusionTableRadius(map);
            }
            else
            {
            	url = queryLandsatFusionTableCells(map, cellrange);
            }
  			//url.push(encodedQuery);
			//url.push('&callback=drawLandsatGrid');
			//url.push('&key=' + MAPS_API_KEY);
			var script = document.createElement('script');
			script.src = url.join('');
			var body = document.getElementsByTagName('body')[0];
			body.appendChild(script);
		}
	} else {
		if (showlayer === false) {
			console.log("deleting landsat layer script");
			resetInfoWindow();
			gridInitialised = false;
			// var body = document.getElementsByTagName('body')[0];
			script = document.getElementById('script');
			if (script) {
				script.parentElement.removeChild(script); // script is undefined. this is not working.
			}
		}
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

function landsatGrid_mouseover(e) {
	this.setOptions({
		//fillOpacity : 0.3,
		strokeWeight : 5
		//strokeColor : '#FFFFFF',
		
	});
}

function landsatGrid_mouseout(e) {
	this.setOptions({
		fillOpacity : 0,
		strokeWeight : 1
	})
}

function landsatGrid_zoom(e) {
	// needs  work
	if (e.zoom() < 6) {
		landsat_cell.hidden();
	} else {
		landsat_cell.show();
	}
	console.log(e.zoom());
}

function landsatGrid_click(e) {
	console.log('landsatGrid_click()')
	cellobject = YAML.parse(this.get("Description")); //converts the YAML html description to JS object.
	
	selectedPath = parseInt(cellobject['<strong>PATH</strong>'], 10); 
	selectedRow  = parseInt(cellobject['<strong>ROW</strong>'],  10);

	selectedLAT_UL = parseFloat(cellobject['<strong>LAT UL</strong>']);
	selectedLON_UL = parseFloat(cellobject['<strong>LON UL</strong>']);
	selectedLAT_UR = parseFloat(cellobject['<strong>LAT UR</strong>']); 
	selectedLON_UR = parseFloat(cellobject['<strong>LON UR</strong>']);
	selectedLAT_LL = parseFloat(cellobject['<strong>LAT LL</strong>']);
	selectedLON_LL = parseFloat(cellobject['<strong>LON LL</strong>']);
	selectedLAT_LR = parseFloat(cellobject['<strong>LAT LR</strong>']);
	selectedLON_LR = parseFloat(cellobject['<strong>LON LR</strong>']);
	
	//console.log(cellobject['<strong>PATH</strong>'], cellobject['<strong>ROW</strong>']);

	$(landsatgrid_panel).empty();
	htmlString = "<p><font-size:50%;color:blue strong>zoom:</strong> " + 
			 map.getZoom() + "</p>";
	htmlString += "<p>lat: " + 
			map.getCenter().lat().toFixed(3) + 
			", lng: " + 
			map.getCenter().lng().toFixed(3) + "<br>" + 
			"Path: " + parseInt(cellobject['<strong>PATH</strong>'],10) + 
			" Row: " + parseInt(cellobject['<strong>ROW</strong>'],10) +
			"<br></p>"; 

	$(landsatgrid_panel).html(htmlString);
	
	cellSelected(); 
 }

function drawLandsatGrid(data, clickable) {
	"use strict";
	
	var rows = data.rows;
	// var currentBounds = map.getBounds(); // get bounds of the map object's
	// current (initial) viewport
	for ( var i in rows) {
		var infoWindow = new google.maps.InfoWindow();
		infoWindowArray.push(infoWindow);

		// console.log(data);
		var newCoordinates = [];
		var geometry = rows[i][1].geometry;
		
		if (geometry) {
			newCoordinates = constructNewCoordinates(geometry);
			var description = rows[i][2];
			
			var cellobject = YAML.parse(description); //converts the YAML html description to JS object.
			
			selectedPath = parseInt(cellobject['<strong>PATH</strong>'], 10); 
			selectedRow  = parseInt(cellobject['<strong>ROW</strong>'],  10);
			console.log("drawLandsatGrid() path %d, row %d", selectedPath, selectedRow)
			//colour as checkerboard
			var cell_colour
			if ((selectedPath %2) == (selectedRow %2)) //both path and row are odd or they are both even. 
				{
					cell_colour = '#CCFFFF'
				}
			else
				{
					cell_colour = '#FFFFCC'
				}

			var landsat_cell = new google.maps.Polygon({
				paths : newCoordinates,
				strokeColor : cell_colour,
				strokeOpacity : 0.4,
				strokeWeight : 1,
				fillOpacity : 0,
				editable : false,
				clickable : landsatgrid_isclickable,
				suppressInfoWindows : true,
				goedesic: true,
				// pointer-events: none,
				content : description
			});
			//add non standard new attributes
			landsat_cell['path'] = selectedPath,
			landsat_cell['cell'] = selectedRow,

			landsat_cell.set("Description", description); // Add attributes
															// for adding
															// description into
															// polygon.

			landsat_overlays.push(landsat_cell);

			google.maps.event.addListener(landsat_cell, 'click',	landsatGrid_click );
			google.maps.event.addListener(landsat_cell, 'mouseover',	landsatGrid_mouseover );
			google.maps.event.addListener(landsat_cell, 'mouseout', landsatGrid_mouseout);
			google.maps.event.addListener(landsat_cell, 'zoom', landsatGrid_zoom);
			//google.maps.event.addListener(landsat_cell, 'click', landsatGrid_click);

			landsat_cell.setMap(map);

			$(landsatgrid_panel).collapse('show');
		} // if geometry
		else {
			console.log("no geometry ", i);
		}
	} // each row
	console.log(landsat_overlays);

}// drawLandsatGrid

function constructNewCoordinates(polygon) {
	"use strict";
	
	var newCoordinates = [];
	var coordinates = polygon['coordinates'][0];
	for ( var i in coordinates) {
		newCoordinates.push(new google.maps.LatLng(coordinates[i][1],
				coordinates[i][0]));
	}
	return newCoordinates;
}

// function GetPolygonBounds(poly ) {
// No longer called because intersection filter is done in the server, not
// browser.
// var bounds = new google.maps.LatLngBounds();
// var paths = poly.getPaths();
// var path;
// for (var p = 0; p < paths.getLength(); p++) {
// path = paths.getAt(p);
// for (var i = 0; i < path.getLength(); i++) {
// bounds.extend(path.getAt(i));
// }
// }
// return bounds;
// }

