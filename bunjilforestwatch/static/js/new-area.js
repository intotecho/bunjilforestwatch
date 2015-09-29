/**
 * @name new-area
 * @version 1.0
 * @author Chris Goodman 
 * @copyright (c) 2012-2015 Chris Goodman 
 * @fileoverview Shows a map and allows user to create a new area.
 */

var bunjil = function() {
	
}; //my global variable.

var draw_boundary_instructions = 
	"<li><b>How to draw a boundary</b></li>" + 
	"<li>Drag  the map so that its center is roughly over your area. " + 
	"Or type the name of your region into the Search Box and the map center on it.</li>" + 
	"<li>Zoom the map till whole area takes up most of the view.</li>" + 
	"<li>Tick the <b>Landsat Grid</b> checkbox to see where landsat images will overlap.</li>" + 
	"<li>Create markers by clicking around the boundary in an <b>anticlockwise</b> direction.</li> " +
	"<li>When you have gone right around, click on the first marker to close the area.</li>" +
	"<li>Check the shape of your area, you can adjust it by dragging the small circles.</li>" + 
	"<li>Click _Oops! Restart_ if you made a mistake.</li>" +  
	"<li>When you are done, Recheck your zoom and map center to best show your area..</li>"  +
	"<li>Finally click <b>Create Area</b>.</li>" ;

var fusion_table_instructions= 
	"<li><b>How to import a fusion table</b></li>" + 
	"<li>The fusion table must either be public or shared with this bunjil's service account. </li>";

/**
 * called when user clicks Create Area.
 * pulls data from the form and validates it. 
 * pulls boundary from the map or fusion table 
 * sends new area request to server.
 * @param map
 */
function createArea(map)
{
	"use strict";
	var problems = "";
	var area_name =  $('#area_name').val();
	var area_descr =  $('#area_descr').val();
	var area_boundary_ft =  $('#boundary_ft').val();

	var selection = $('input[name=opt-fusion]:checked', '#new_area_form').val();

	// form validation
	if ((null === area_name) || (area_name === "")) {
		problems += 'Please give your area a short name<br/><br/>';
	}
	if ((null === area_descr) || (area_descr === "")) {
		if (problems.length > 0) {
			problems += 'Giving  your area an optional description helps others know why it should be monitored.<br/><br/>';
		}   
	}
	if(selection === 'is-fusion') {
		if ((null === area_boundary_ft  )|| (area_boundary_ft === "" )) {
			problems += 'Please provide a fusion table id.<br/><br/>';
		}
	}
	else if(selection === 'is-drawmap')  {
		if (map.drawingOverlay === null) {
			problems += 'Please mark out the boundary of your area or provide a fusion table id.<br/><br/>';
		}
	}    
	else {
		problems += 'Please select either fusion table or draw map.<br/><br/>';
	}
	/* global bootbox */
	if (problems.length > 0) {
		bootbox.dialog({
			message: problems,
			title: "Please fix these problems and then click <i>Create Area</i>",
			buttons: {
				success: {
					label: "OK",
					className: "btn-info",
				}
			}
		});
		return;
	}
	
	// get and send the viewing parameters of the map
	var unwrapped_mapcenter = map.getCenter(); // can exceed 90lat or 180 lon
	var mapcenter = new google.maps.LatLng(unwrapped_mapcenter.lat(), unwrapped_mapcenter.lng()); //wrapped.
	var mapzoom = map.getZoom();
	var newArea;
	if(selection === 'is-drawmap')  {
		newArea = { "type": "FeatureCollection",
					"features": [
			             { "type": "Feature",
			            	 "geometry":   {"type": "Point", "coordinates": [mapcenter.lat(), mapcenter.lng()]},
			            	 "properties": {"featureName": "mapview", "zoom": mapzoom }
			             },
			             { "type": "Feature",
			            	 "geometry":   {"type": "Polygon","coordinates": boundaryPoints},
			            	 "properties": {"featureName": "boundary"}
			             }
			          ],
					 "boundary_ft": area_boundary_ft
		}// End newArea
		map.data.forEach(function(feature, map_p){
			feature.properties.featureName = "boundary";
			newArea.features.append(feature);
		});
	}  
	else {
		newArea = { 
				"boundary_ft": area_boundary_ft
		}
	}

	var toServer = JSON.stringify(newArea);
	document.getElementById("coordinates_id").value = toServer;
	$("#new_area_form").submit();

} /* end-of-createArea*/       


function drop_marker(map, position, name) {
	"use strict";
	/* Get the icon, place name, and location.*/
	var image = {
			url: '/static/img/cross-hair-target-col.png', //place.icon
			size: new google.maps.Size(100, 100),
			origin: new google.maps.Point(0, 0),
			anchor: new google.maps.Point(17, 34),
			scaledSize: new google.maps.Size(40, 40)
	};
	
	// Create a marker for each place.
	var marker = new google.maps.Marker({
		map: map,
		icon: image,
		draggable: true,
		title: name,  //place[0].name,
		position: position, // place[0].geometry.location,
		animation: google.maps.Animation.DROP
	});
}

/**
 * Centers map over place, zooms to 9 and drops a big marker.
 *
 * @param place comes from searchBox.getPlaces();
 */

function zoomToPlace(map, place) {
	"use strict";
	if ((place === null) || (place === undefined)) {
		return;
	}
	
	var len = place.length;
	if (len === 0) {
		return; // nothing found, so nothing to do.
	}
	if (len > 1) {
		console.log("SearchBox returned multiple hits - taking first only");
	}
	
	drop_marker(map, place[0].geometry.location, place[0].name);
	map.setCenter(place[0].geometry.location);
	map.setZoom(9);
	
	// remove any points that have been drawn.
}

function cannot_zoom_to_position(error) {
	"use strict";
	var msg;
	switch(error.code) {
    case error.PERMISSION_DENIED:
    	msg = "User denied the request for Geolocation.";
        break;
    case error.POSITION_UNAVAILABLE:
    	msg= "Location information is unavailable.";
        break;
    case error.TIMEOUT:
    	msg = "The request to get user location timed out.";
        break;
    case error.UNKNOWN_ERROR:
    	msg = "An unknown error occurred.";
        break;
	}
	$('#zoom-here-help').html(msg);
}

/**
 * Zoom the map to the user's current position
 * @returns
 */
function zoom_here(map, event) {
	"use strict";
    event.preventDefault();

	if (navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(function(position) {
			 var initialLocation = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
			 map.setCenter(initialLocation);
			 map.setZoom(9);
			},
			cannot_zoom_to_position);
	}
	else {
		console.log('browser has no navigator');
	}
}


function drop_pin_mode(map, event) {
	"use strict";
    event.preventDefault();
    $('#drop-pin-mode').addClass('btn-default').removeClass('btn-primary');
    $('#move-map-mode').addClass('btn-primary').removeClass('btn-default');

    // Display div for next instruction.
    $('#drop-pin-label').hide();
    $('#drop-pin-help').hide();
    $('#move-map-help').show();
    $('#move-map-label').show();

    // Call drawing-tools to set map drawing mode to drop pin
    map.drawingTools.drawCenterPointMarker(map);    
}

function move_map_mode(map, event) {
	"use strict";
	event.preventDefault();
    $('#move-map-mode').addClass('btn-default').removeClass('btn-primary');
    $('#drop-pin-mode').addClass('btn-primary').removeClass('btn-default');

    // Display div for next instruction.
    $('#drop-pin-label').show();
    $('#drop-pin-help').show();
    $('#move-map-help').hide();
    $('#move-map-label').hide();
    
    // Turn of Draging Mode byt keep markers
    map.drawingTools.stopDrawCenterPointMarker(map);    
    
}

function scroll_to_target(scroll_target) {

	"use strict";
	var t = $("html,body");
	var html = $("html");
	var body = $("body");
	
	console.log('before animate' + t.scrollTop());
	console.log('before html' + html.scrollTop());
	console.log('before body ' + body.scrollTop());
	t.animate(
		    { scrollTop: scroll_target.offset().top}, 1000 
		    /*
		     * ,
		    {
		        complete : function(){
		        	console.log('after animate' + t.scrollTop());
		    		console.log('before html' + html.scrollTop());
		    		console.log('before body ' + body.scrollTop());
		        	}
		    }
		    */
		);
}



/**
 * initialize_map.initialized  ensures it may be called repeatedly.
 * The map is only created once. 
 * Each time its called it can move the map to a new place.
 * @param place
 */
function initialize_map(place) {
	"use strict";
	if (initialize_map.map !== null) {
		console.log("reinitialize map");
		zoomToPlace(initialize_map.map, place);
		return;
	}

	// server sets a default center based on browser provided coordinates.
	var center_pt = $('#latlng').text().split(','); //TODO: Refactor using area_json

	var mapOptions = {
			center: new google.maps.LatLng(center_pt[0], center_pt[1]),
			zoom: 3,
			overviewMapControl: true,
			mapTypeId: google.maps.MapTypeId.HYBRID
			//drawingMode: 'Point',
	};
	var map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);
	
	initialize_map.map = map;   // don't do this more than once.
	map.drawingOverlay = null; // no user drawn shape yet. 
	//map.drawingManager  = createDrawingManager(map, google.maps.drawing.OverlayType.POLYGON);

	var mapContainer = document.getElementById('map-canvas-c');
	var dropContainer = document.getElementById('drop-container');
	var geoJsonPanel = document.getElementById('geojson-panel');
	var geoJsonInput = document.getElementById('geojson-input');
	var downloadLink = document.getElementById('download-link');
	
	/* global DrawingTools */
	map.drawingTools = new DrawingTools(map, mapContainer, dropContainer, geoJsonPanel, geoJsonInput, downloadLink);

	$('#zoom-here').click(function(event) {
		zoom_here(map, event);
		});

	$('#drop-pin-mode').click(function(event) {
		drop_pin_mode(map, event);
	});

	$('#move-map-mode').click(function(event) {
		move_map_mode(map, event);
	});

	/*function to add the polygon coordinates to the form data prior to submit.*/ 
	$('#createarea_id').click(function(){ 
		createArea(map);
	});		

	//Oops! Redraw
	$('#reset_id').click(function(){ 
		//map.creator.destroy();
		//map.creator=new PolygonCreator(map);
	});		 

	//show paths
	$('#showData').click(function(){ 
		console.log("map-panel draw");
		$('#map_panel').empty();
		if(null === map.drawingOverlay){
			$('#map_panel').append('Please mark out your area first, then click Create Area');
		}
		else {
			$('#map_panel').append("TODO coords");
		}
	});

	//Checkbox to show/hide overlays  		
	/* global createLandsatGridOverlay */
	$('.layer').click(function(){
		var layerID = parseInt($(this).attr('id'));

		if ($(this).is(':checked')){
			if(layerID === 0)
			{
				createLandsatGridOverlay(map, 0.5, false, null);
			}
		} 
		else {
			if(layerID === 0) {
				createLandsatGridOverlay(map, 0, true, null);
			}
		}
	});

	google.maps.event.addListener(map, 'bounds_changed', function() {

		if (map.getZoom() > 6) {
			console.log ("Show Landsat Grid");
			createLandsatGridOverlay(map, 0.5, false, null);
		}
	});

	google.maps.event.addListener(map, 'idle', function() {
		var scroll_target = $('#scroll-to-here');
		scroll_to_target(scroll_target);
		
		//This is needed so the fusion tables query works
		var map_center = map.getCenter();
		if (map_center.lng() < -180) { 
			map.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng()+360));
		}
		if (map_center.lng() > 180) { 
			map.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng() - 360));
		}
	});

	/*
	google.maps.event.addListener(map.drawingManager, 'poloygoncomplete', function(polygon) {
		  var x = polygon;
	});
	
	
	google.maps.event.addListener(map.drawingManager, 'overlaycomplete', function(event) {
				
		  if (event.type == google.maps.drawing.OverlayType.POLYGON) {
			  
			  map.drawingOverlay = event.overlay;
			  
			  //var len = map.drawingOverlay.getPath().getLength();
			  var path = map.drawingOverlay.getPath();
			  var len = path.getLength();
			  
		      for (var p = 0; p < len; p++) {
		            console.log(path.getAt(p).toUrlValue(7));
		      }
		  }
	});
	*/
	if (place !== null){
		zoomToPlace(map, place);
	}
	return map;
}
initialize_map.map = null;


/**
 *Listen for the event fired when the user selects an item from the
	   pick list. Retrieve the matching places for that item. 
	   Although this supports multiple markers we only want one. 
 * @param map
 * @param searchBox
 */
function searchPlaceSelected(map, searchBox){
	"use strict";
	var place = searchBox.getPlaces();
	initialize_map(place);
}

/**
 * Get the user's broad region. 
 * As supplied by the browser's 'navigator.geolocation' object.
 * 
 * Used to Bias the place search results to the user's geographical location,
 */

function biasSearchToUserRegion(searchBox, accuracy) {
	"use strict";
	if (navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(function(position) {
			var geolocation = {
					lat: position.coords.latitude,
					lng: position.coords.longitude
			};
			var circle = new google.maps.Circle({
				center: geolocation,
				radius: accuracy
			});
			searchBox.setBounds(circle.getBounds());
		});
	}
}



/**
 * Create a search box on the google map for search for places 
 * and link it to the UI element.
 * When a place is selected, draw a cross hair placemarker, 
 * Then goto that place with a zoom of 9 
 * @param map {google.map}
 * @returns {google.maps.places.SearchBox}
 */

function addSearchBox(map)
{
	"use strict";

	var input = /** @type {HTMLInputElement} */(
			document.getElementById('searchbox_id'));
	
	//map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
	var searchBox = new google.maps.places.SearchBox(
					/** @type {HTMLInputElement} */(input));

	
	/*  bias the search to places in the user's broad region */
	biasSearchToUserRegion(searchBox,1000);
	
	// When the user selects an address from the dropdown, call searchPlaceSelected
	searchBox.addListener('places_changed', function() {
	    searchPlaceSelected(map, searchBox);
	});

	return searchBox;
}
	


/**
 * Initialises the form for new-area page, but not yet the map.
 */




/**
 * Pre-Checks if all inputs are provided to enable create button
 * This occurs as user is entering details so should not be intrusive
 */

function pre_checkform_next_area(event) {
	"use strict";
	var problems = "";
	var area_name =  $('#area_name').val();
	var shared = $('input[name=opt-sharing]:checked', '#new_area_form').val();
	var self_monitor = $('input[name=self-monitor]:checked', '#new_area_form').val();
	var request_volunteers = $('input[name=request-volunteers]:checked', '#new_area_form').val();
	var accept = $('input[name=accept]:checked', '#new_area_form').val();

	// form validation
	if ((null === area_name) || (area_name === "")) {
		problems += 'Give your area a short name<br/><br/>';
	}
	if(shared === undefined) {
			problems += 'Choose public, private or inlisted.<br/><br/>';
	}
	if((self_monitor === undefined) && (request_volunteers === undefined)) {
		problems += 'Either choose to monitor your self or request volunteers.<br/><br/>';
	}
	if(accept !== "true") {
		problems += 'To register an area you must agree to investigate reports in your area.<br/><br/>';
	}
	if(area_name === '@'){ //test code
		$('#map-row').show();
		var target = $('#map-find');
		target.show();
		initialize_map(null);
		return "";
	}
	if (problems.length > 0) {
		$('#next-area').addClass('btn-default').removeClass('btn-primary');
	}
	else {
		$('#next-area').removeClass('btn-default').addClass('btn-primary');
	}
	return problems;
}

	
/**
 * Checks if all inputs are provided to enable create button
 */
function checkform_next_area(event) {
	"use strict";	
	event.preventDefault();

	var problems = pre_checkform_next_area(event);
	
	$('#form-errors').html(problems);
	if (problems.length === 0) {
		$('#map-row').show();
		var target = $('#map-find');
		target.show();
		initialize_map(null);
	}
}	

/**
 * Stop ENTER generating a submit form.
 */
$(document).ready(function() {
	"use strict";
	$('form input').keydown(function(event){
	    if(event.keyCode === 13) {
	      event.preventDefault();
	      return false;
	    }
	  });
	});

function init_fusionform()
{
	"use strict";
	var selection = $('input[name=opt-fusion]:checked', '#new_area_form').val();
	if((selection === 'is-fusion') || (selection === 'is-drawmap')) {
		initialize_map(null);

		$('#createarea_id').fadeIn();

		if (selection === 'is-fusion') {
			$('#drawmap-form-c').fadeOut();
			$('#fusiontable-form-c').fadeIn();
			$('#boundary-instructions').html(fusion_table_instructions).fadeIn();
			$('#reset_id').fadeOut(); // Oops button
		} 
		else {
			$('#drawmap-form-c').fadeIn();
			$('#fusiontable-form-c').fadeOut();
			$('#boundary-instructions').html(draw_boundary_instructions).fadeIn();
			$('#reset_id').fadeIn(); // Oops button
		}   
	}	
}

function initialize_new() {
	"use strict";

	var searchBox = addSearchBox();
    
    /* Radio Button Handler - Select Fusion or Draw Map */

	$('#new_area_form input').on('change', pre_checkform_next_area);
	
	$('#next-area').click(checkform_next_area);

	/** -- resize the map div - This uses a tip from //github.com/twitter/bootstrap/issues/2475 --> 
	$(window).resize(function () {
		var h = $(window).height();
		var offsetTop = 60; // Calculate the top offset
		$('#map-canvas').css('height', (h - offsetTop));	        
	}).resize();   
    ***/
}

google.maps.event.addDomListener(window, 'load', initialize_new);
