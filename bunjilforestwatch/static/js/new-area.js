/**
 * @name new-area
 * @version 1.0
 * @author Chris Goodman 
 * @copyright (c) 2012-2015 Chris Goodman 
 * @fileoverview Shows a map and allows user to create a new area.
 */

var area_json = null; // WARNING only defined after a successful save returns an area object.

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
 * @returns returns the area_area in the input text control.
 */
function get_area_name() {
	var area_name = $('#area_name').val();
	if(typeof(area_name) === 'undefined') 
	{
		area_name = '';
	}
	//console.log('area_name: ', area_name);
	return area_name;
}

/**
 * @returns one of 'not_selected', 'private', 'unlisted' or 'shared'.
 */
function get_shared() {
	//var shared = $('input[name=opt-sharing]:checked', '#sharingAccord').val();
	var shared  = $('#sharingAccord input:radio:checked').val();
	if(typeof(shared) === 'undefined') 
	{
		shared = 'not_selected';
	}
	//console.log('shared: ', shared);
	return shared;
}

/**
 * @returns true if the 'Self-monitor' control is ticked, else false.
 */
function get_self_monitor() {
	var self_monitor = $('input[name=self-monitor]:checked').val() === 'true'? true:false;
	console.log('self_monitor: ', self_monitor);
	return self_monitor;
}


/**
 * @returns true if the 'Community monitoring' control is ticked, else false.
 */
function get_request_volunteers() {
	var request_volunteers = $('input[name=request-volunteers]:checked').val() === 'true'? true:false;
	console.log('request_volunteers: ', request_volunteers);
	return request_volunteers;
}

/**
 * @returns true if user has ticked the areement, else false.
 */
function get_has_accepted() {
	var accepted = $('input[name=accept]:checked', '#new_area_form').val() === "true" ? true:false;
	//console.log('has accepted : ', accepted);
	return accepted;
}

function get_descr_what() {
	var val = $('#area_descr_what_text').val();
	if (typeof val === 'undefined') 
		return ""; 
	else return val;
}

function get_descr_who() {
	var val = $('#area_descr_who_text').val();
	if (typeof val === 'undefined') 
		return ""; 
	else return val;
}
function get_descr_why() {
	var val = $('#area_descr_why_text').val();
	if (typeof val === 'undefined') 
		return ""; 
	else return val;
}

function get_descr_how() {
	var val = $('#area_descr_how_text').val();
	if (typeof val === 'undefined') 
		return ""; 
	else return val;
}

function get_threats() {
	var val = $('#area_descr_threats_text').val();
	if (typeof val === 'undefined') 
		return ""; 
	else return val;
}

function get_area_wiki() {
	var val= $('#area-wiki').val();
	if (typeof val === 'undefined') 
		return ""; 
	else return val;
}



/**
 * Called when user clicks Create Area.
 * Pulls data from the form and validates it. 
 * Pulls boundary from the map or fusion table. 
 * Sends new area request to server.
 * @param map
 */
function save_area(map, is_update)
{
	"use strict";
	var area_name =  get_area_name();
	var shared = get_shared();
	var self_monitor = get_self_monitor();
	var request_volunteers = get_request_volunteers(); //$('input[name=request-volunteers]', '#new_area_form').val();
	var accept = get_has_accepted();
	
	// get and send the viewing parameters of the map
	var unwrapped_mapcenter = map.getCenter(); // can exceed 90lat or 180 lon
	var mapcenter = new google.maps.LatLng(unwrapped_mapcenter.lat(), unwrapped_mapcenter.lng()); //wrapped.
	var mapzoom = map.getZoom();
	
	var selection = $('input[name=opt-fusion]:checked', '#new_area_form').val();
	var boundary_type = "none"; 
	var area_boundary_ft =  $('#boundary_ft').val();
	
	if (typeof selection === 'undefined') {
		boundary_type = 'none'; 
	} 
	else if(selection === 'is-fusion') {
		boundary_type = 'fusion';   
		if ((null === area_boundary_ft  )|| (area_boundary_ft === "" )) {
			//problems += 'Please provide a fusion table id.<br/><br/>';
		}
	}
	else if(selection === 'is-drawmap')  {
		boundary_type = 'geojson';
		if (map.drawingOverlay === null) {
			//problems += 'Please mark out the boundary of your area or provide a fusion table id.<br/><br/>';
		}
	}    
	
	var new_area_geojson = { "type": "FeatureCollection",
				"properties": {
					"area_name":area_name,
					"shared" :	shared,
					"self_monitor" : self_monitor,
					"request_volunteers" : request_volunteers,
					"accept" : accept,
					"boundary_type": "none", //{How is boundary defined? none, fusion, geojson} 
					// "area_url" : 'server sets',
					// 'owner': 'server sets' 
					
					"area_description": {
						   "description": 	  get_descr_what(),
						   "description_why": get_descr_why(),
						   "description_who": get_descr_who(),
						   "description_how": get_descr_how(),
						   "threats": 		  get_threats(),
						   "wiki": 			  get_area_wiki()
					},
					"fusion_table": {
						   //"ft_link": server sets,
							//"ft_docid": server sets,
							 "boundary_ft": area_boundary_ft
					 }
				},
				"features": [
		             { "type": "Feature",
		            	 "geometry":   {"type": "Point", "coordinates": [mapcenter.lng(), mapcenter.lat()]},
		            	 "properties": {"featureName": "mapview", "zoom": mapzoom }
		             }
		             /*//added below
		             { "type": "Feature",
		            	 "geometry":   {"type": "Polygon","coordinates": location_feature.geometry},
		            	 "properties": {"featureName": "boundary"}
		             }
		             */
		          ]
				
	}; // End new_area_geojson

	if (typeof map.drawingTools.area_location !== 'undefined') {
		var location_feature = map.drawingTools.area_location.features[0];
		location_feature.properties.featureName = 'area_location';
		new_area_geojson.features.push(location_feature);
	}
	else {
		console.log('save_area() Error: no location set');
	}

	var data_to_post = JSON.stringify(new_area_geojson);

	if(is_update) {
		//replace the entire area with this update".
		$.ajax({
		      type: "PUT",
		      url: "area",
		      data: 'new_area_geojson_str='+ data_to_post,
		      success: function() {
		    	  alert('Area Updated OK');
		      },
		      error: function(requestObject, error, errorThrown) {
	 	            alert(errorThrown);
	 	            console.log(error, errorThrown);
		      }
		    });
	}
	else {
		//create a new area
		toastr.clear();
		
		$('#save-wait-popover').popoverX({
	            target: '#save-area'  //container
	    });
		$('#save-wait-popover').popoverX('show');
		 
	    $('#close-dialog-save-area-wait').click(function(){    
	        $('#save-wait-popover').popoverX('hide');
	    });
	    
		var xhr = $.ajax({
		      type: "POST",
		      url: "area",
		      data: 'new_area_geojson_str='+ data_to_post,
		      success: function(data) {
		    	  $('#save-wait-popover').popoverX('hide');
	 	          addToasterMessage('alert-success','Area ' + area_name + ' created OK');
	 	          area_json = JSON.parse(data);
	 	          var url = area_json.properties.area_url
		    	  saved_area(url);
		      },
		      error: function(requestObject, error, errorThrown) {
		    	  	$('#save-wait-popover').popoverX('hide');
		    	  	var msg = 'Error ' + requestObject.status + ' ' + requestObject.statusText + ' ' + requestObject.responseText;
	 	            console.log(msg);
	 	            addToasterMessage('alert-danger', msg);
		      }
		    });
	}   
	return false; //don't call more event handlers
} /* end-of-save_area*/       

/**
 * After submitting the location name and sharing options, ask user for more details
 * @param map
 */
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
	/*
	if (typeof place === 'LatLng')
	{
			return;
	}
	*/
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
    /*
      
     if (typeof(event) !== 'undefined') {
		event.preventDefault();
	}
	*/
    //console.log(map.getZoom());
	if(map.getZoom() < 7) {
			//too far out 
		 	$('#zoom-more-popover').show();
		 	return;
	}
	else {
		 $('#zoom-more-popover').hide();

	}
    // Display div for next instruction.
    $('#mark-map-form').show();
    $('#move-map-form').show();
    $('#drag-map-form').hide();
    $('#save-area-form').hide();
 
    
    // Call drawing-tools to set map drawing mode to drop pin
    map.drawingTools.drawCenterPointMarker(save_map_mode);    
}




function scroll_to_target(scroll_target) {
	"use strict";
	var t = $("html,body");
	t.animate(
		    { scrollTop: scroll_target.offset().top}, 800 
		);
}


function resizeEditor() {
	"use strict";
	var row_height = $('#map-canvas-c').height();
	var height = row_height - $('#geojson-controls').height() - 8 + "px";
	$('.CodeMirror').height(height);	
}




/**
 * initialize_map.initialized  ensures it may be called repeatedly.
 * The map is only created once. 
 * Each time its called it can move the map to a new place.
 * @param place
 */
function initialize_map(place, center_prm) {
	"use strict";
	if (initialize_map.map !== null) {
		console.log("reinitialize map");
		zoomToPlace(initialize_map.map, place);
		return;
	}
	
	// server sets a default center based on browser provided coordinates.
	var center_pt;
	var init_zoom = 3;
	
	if(center_prm !== null) {
		center_pt = center_prm;
		init_zoom = 7;
	}
	else {
		//use location from server.
		var center = $('#latlng').text().split(','); //TODO: Refactor using area_json
		center_pt =  new google.maps.LatLng(center[0], center[1]);
	}
	
	var mapOptions = {
			center: center_pt,
			zoom: init_zoom,
			overviewMapControl: true,
			mapTypeId: google.maps.MapTypeId.HYBRID
	};
	var map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);
	
	initialize_map.map = map;   // don't do this more than once.
	map.drawingOverlay = null; // no user drawn shape yet. 

	var mapContainer = document.getElementById('map-canvas-c');
	var dropContainer = document.getElementById('drop-container');
	var geoJsonPanel = document.getElementById('geojson-panel');
	var geoJsonInput = document.getElementById('geojson-input');
	var downloadLink = document.getElementById('download-link');
	
	/* global DrawingTools */
	map.drawingTools = new DrawingTools(map, mapContainer, dropContainer, geoJsonPanel, geoJsonInput, downloadLink);
	
	//$('#zoom-help-popover["clickover"]').popoverx({ fire_on : 'hover', hover_delay_close: 3000 });

	$('#syntax-errors-popover-close').click(function(event) {
	 	event.preventDefault();
	 	$('#syntax-errors-popover').popoverX('hide');
	});

	/* ZOOM-MORE-POPOVER */
	$('#zoom-more-popover-close').click(function(event) {
	 	event.preventDefault();
	 	$('#zoom-more-popover').popoverX('hide');
	});

	/* ZOOM-HELP-POPOVER */

	$('#zoom-help-popover-close').click(function(event) {
	 	event.preventDefault();
	 	$('#zoom-help-popover').popoverX('hide');
	});

	
	/* DRAG-HELP-POPOVER */
	$('#drag-help-popover-close').click(function(event) {
	 	event.preventDefault();
	 	$('#drag-help-popover').popoverX('hide');
	});
	
	/* ZOOM-HELP */
	$('#zoom-here').click(function(event) {
		zoom_here(map, event);
	});

	$('#drop-pin-mode').click(function(event) {
		drop_pin_mode(map, event);
	});

	$('#move-map-mode').click(function(event) {
		move_map_mode(event);
	});

	$('#clear-map').click(function(event) {
		clear_map(event);
	});

	/*function to add the polygon coordinates to the form data prior to submit.*/ 
	$('#save-area').click(function(event){ 
		event.preventDefault();
		save_area(map, false);
	});		

	$('#update-area').click(function(event){ 
		event.preventDefault();
		updateArea(map, true);
	});		
	
	$('#advanced').click(function(event){ 
		toggle_advanced();
	});		

	//Checkbox to show/hide overlays  		
	/* global createLandsatGridOverlay */
	$('#landsat-grid').click(function(){

		if ($(this).is(':checked')){
				
				createLandsatGridOverlay(map, 0.5, false, null);
		} 
		else {
				deleteLandsatGridOverlay(map, 0, true, null);
		}
	
	});

	google.maps.event.addListener(map, 'bounds_changed', function() {
	});

	var scroll_target = $('#scroll-to-here');
	if (typeof map.scroll_once  === 'undefined') {
		map.scroll_once = true;
		scroll_to_target(scroll_target);
	}

	google.maps.event.addListener(map, 'idle', function() {
		
		// Normalize longitude. This is needed so the fusion tables query works
		var map_center = map.getCenter();
		if (map_center.lng() < -180) { 
			map.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng()+360));
		}
		if (map_center.lng() > 180) { 
			map.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng() - 360));
		}
		
		var z = map.getZoom();
		//console.log('zoom: ' + z);
		if (z <= 0) {
			map.setZoom(1);
		}
		deleteLandsatGridOverlay(map, 0, true, null);
		if (z > 6) {
			
			if( $('#landsat-grid').is(':checked') == true) {
				createLandsatGridOverlay(map, 0.5, false, null);
			};
			$('#drop-pin-mode').removeClass('btn-default').addClass('btn-primary');
		}
		else {
			$('#drop-pin-mode').addClass('btn-default').removeClass('btn-primary');
		}
	});
	if (place !== null){
		zoomToPlace(map, place);
	}
	
	
	return map;
}
initialize_map.map = null;

function move_map_mode(event) {
	"use strict";
	if (typeof(event) !== 'undefined') {
		event.preventDefault();
	}
    // Display div for next instruction.
    $('#drag-map-form').show();
    $('#mark-map-form').hide();
    $('#save-area-form').hide();
    $('#move-map-form').hide();
    
    // Turn of Dragging Mode
    var map = initialize_map.map;
    map.drawingTools.stopDrawCenterPointMarker();
}


function clear_map(event) {
	"use strict";
	if (typeof(event) !== 'undefined') {
		event.preventDefault();
	}
    // Display div for next instruction.
    $('#drag-map-form').show();
    $('#mark-map-form').hide();
    $('#save-area-form').hide();
    $('#move-map-form').hide();
    
    var map = initialize_map.map;
    // Remove Marker
    map.drawingTools.removeCenterPointMarker(); 
}
function save_map_mode() {
	"use strict";
	
	// Display div for next instruction.
	$('#save-area-form').show();
	$('#move-map-form').show();
	$('#drag-map-form').hide();
    $('#mark-map-form').hide();
    
    // Turn of Draging Mode but keep markers
    var map = initialize_map.map;
    map.drawingTools.stopDrawCenterPointMarker(map); 
    
    var locn_string = map.drawingTools.geoJsonInput.value;
}

function initialize_geojson_editor()
{
	"use strict";
	/* global CodeMirror */
	if (typeof initialize_map.editor === 'undefined') {
		initialize_map.editor = CodeMirror.fromTextArea(document.getElementById('geojson-input'),  {
		    lineNumbers: true,
		    indentUnit: 0,
		    tabSize: 0,
		    scrollbarStyle: 'overlay',
		    mode: "application/json",
		    gutters: ["CodeMirror-lint-markers"],
	        theme: 'midnight', 
	        autofocus: (window === window.top),
	        lint: true,
		    lintWith: CodeMirror.jsonValidator,
		    lintOnChange: true,
	        matchBrackets: true
		  }); 	

		$('#select-all').click(function (e){
			initialize_map.editor.execCommand('selectAll');		
		});
		
		$('#download-area').click(function (e){
			  var link = $('#download-link'); 
			  link.download = name;
			  link.click();
		});
		
		function downloadURI(uri, name) {
		}
		
		initialize_map.editor.on("changes", function (editor, changes) {
		   /* load editor with current drawing on map */
		  initialize_map.map.drawingTools.refreshDataFromGeoJson();
		  return true;
		});
		initialize_map.map.drawingTools.refreshGeoJsonFromData();
		google.maps.event.addDomListener(window, 'resize', resizeEditor);
		resizeEditor();
	}
}

/**
 * Display or Hide the GeoJson editor alongside the map
 */
function toggle_advanced() { 
	"use strict";

	var map_column = $('#map-column');
	map_column.toggleClass('col-md-9').toggleClass('col-md-12');
	if (map_column.hasClass('col-md-12')) {
		$('#geojson-column').hide();
	}
	else {
		$('#geojson-column').show();
		initialize_geojson_editor();
	}
}	


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
	initialize_map(place, null);
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


var BJTEST = BJTEST || {};

BJTEST.subns = (function() {
	"use strict";
	
    var internalState = "Message";

    var privateMethod = function() {
        // Do private stuff, or build internal.
        return internalState;
    };
    
    var initAdvancedMap = function() {
		var area_name =  get_area_name(); 
		var shared = get_shared(); 
		var self_monitor = get_self_monitor(); 
		var request_volunteers = get_request_volunteers();
		var accept = get_has_accepted(); 

		$('#map-row').show();
		if (area_name.length < 3) {
			area_name = 'Test Area ' + Math.floor((Math.random() * 999) + 1);
    		$('#area_name').val(area_name);
		}

		if(shared === 'not_selected') {
			$('input[value=shared]', '#new_area_form').prop('checked', true);
			shared = 'shared';
		}

		$('#area_descr_what_text').val('A test area created by initAdvancedMap()');
		$('#area-wiki').val('http://bunjilforestwatch.net');

		$('#accept').prop('checked', true);

		$('#locate-accordion').show();
		
		var center_pt =  new google.maps.LatLng(-33.8, 151.47); //Blue Mountains NP.
		
		initialize_map(null, center_pt);
		drop_pin_mode(initialize_map.map, null);
		//toggle_advanced();
		return "";
    }
    
    return {
        isTesting: true,
        initAdvancedMap: initAdvancedMap
    };
})();



/**
 * Pre-Checks if all inputs are provided to enable create button
 * This occurs as user is entering details so should not be intrusive
 */
function pre_checkform_next_area(event) {
	"use strict";

	var validations = [];
	var problems = "";
	var target;
	
	//get form values
	var area_name = get_area_name();
	var shared = get_shared();
	var self_monitor = get_self_monitor();
	var request_volunteers = get_request_volunteers();
	var area_wiki = get_area_wiki();
	
	//get controls
	var self_monitor_control = $('input[name=self-monitor]', '#new_area_form');
	var request_volunteers_control = $('input[name=request-volunteers]', '#new_area_form');

	var accept = get_has_accepted();
	
	// form validation
	if ((null === area_name) || (area_name === "")) {
		validations.push({'name':'#area-name-validation', 'value':'Give your area a short name.'});
	}
	else {
		if (checkform_next_area.clicked) { 
			$('#area-name-validation').hide();
		}
	}
	
	if(shared === 'not_selected') {
		validations.push({'name':'#sharing-validation', 'value':'Choose public, private or unlisted.'});
	}
	else {
		if (checkform_next_area.clicked) { 
			$('#sharing-validation').hide();
		}
	}
	
	if((shared === 'private') && (request_volunteers !== false)) {
		self_monitor_control.prop("checked", true).prop('disabled', true);
		request_volunteers_control.prop("checked", false).prop('disabled', true);
	}
	else {
		self_monitor_control.prop('disabled', false);
		request_volunteers_control.prop('disabled', false);
	}

	if((self_monitor !== true) && (request_volunteers !== true)) {
		validations.push({'name':'#monitoring-validation', 'value':'Either self-monitor or request volunteers.'});
	}
	else {
		if (checkform_next_area.clicked) { 
			$('#monitoring-validation').hide();
		}
	}
	
	if ((area_wiki !== "") && (isURL(area_wiki) !== true))
	{
		validations.push({'name':'#area-wiki-validation', 'value':'Link is not a valid URL. If unsure, leave this blank.'});
		$('#area-wiki-validation').hide();
	}
	else {
		if (checkform_next_area.clicked) { 
			$('#area-wiki-validation').hide();
		}
	}
	
	if(accept !== true) {
		validations.push({'name':'#accept-validation', 'value':'To register an area you must agree to investigate reports in your area.'});
	}
	else {
		$('#accept-validation').hide();
	}

	if(area_name[0] === '@'){ //test code
		$('#locate-accordion').show();
		$('#map-row').show();
		initialize_map(null, null);
		return "";
	}
	
	
	if(area_name[0] === '!'){ //test code
		BJTEST.subns.initAdvancedMap();
	}
	
	if (validations.length > 0) {
		$('#next-area').addClass('btn-default').removeClass('btn-primary');
	}
	else {
		$('#next-area').removeClass('btn-default').addClass('btn-primary');
		$('#form-errors').html(' ');
	}
	return validations;
}
	
var test_message = 1;

function areanameAccord_setTitle() {
	var area_name = get_area_name();
	var div = $('#areanameAccord_title');
	div.find('.collapsed-content-info').html(area_name);
	if (area_name.length > 0) 
		div.find('.asterix').hide(); 
	else 
		div.find('.asterix').show();
}

function areanameAccord_clicked(event) {
	$('#areanameAccord').collapse('toggle');
	areanameAccord_setTitle();
}

function sharingAccord_setTitle() {
	var share = get_shared();
	var div = $('#sharingAccord_title');
	div.find('.collapsed-content-info').text(share);
	if (share === 'not_selected') 
		div.find('.asterix').show(); 
	else 
		div.find('.asterix').hide();
}

function sharingAccord_clicked(event) {
	$('#sharingAccord').collapse('toggle');
	sharingAccord_setTitle();
}

function monitoringAccord_setTitle() {
	var self_monitor =  get_self_monitor(); 		   
	var request_volunteers = get_request_volunteers(); 
	
	var title = ""; 
	if(self_monitor === true) {
		title += "Self Monitoring";
		if(request_volunteers === true) {
			title += " and Requesting Volunteers help";
		}
		else {
			title += " only";
		}
	}
	else {
		if(request_volunteers === true) {
			title += " Not self monitoring, requesting volunteers";
		}
		else {
			title += "No one will be monitoring this area!";
		}
	}
		
	//console.log(title);
	
	var div = $('#monitoringAccord_title');
	div.find('.collapsed-content-info').text(title);
	//Either self-monitor or request volunteers.
	if((self_monitor === false) && (request_volunteers === false)) {
		div.find('.asterix').show();
	}	
	else {
		div.find('.asterix').hide();
	}
}

function monitoringAccord_clicked(event) {
	$('#monitoringAccord').collapse('toggle');
	monitoringAccord_setTitle();
}

function agreementAccord_setTitle() {
	var accept = get_has_accepted();
	var div = $('#agreementAccord_title');
	
	if(accept === true) {
		div.find('.asterix').hide();
		div.find('.collapsed-content-info').text(' Accepted');
	}	
	else {
		div.find('.asterix').show();
		div.find('.collapsed-content-info').text(' Not accepted');
	}
}

function agreementAccord_clicked(event) {
	$('#agreementAccord').collapse('toggle');
	agreementAccord_setTitle();
}

function descriptionAccord_clicked(event) {
	$('#descriptionAccord').collapse('toggle');
}

function helplocateAccord_clicked(event) {
	$('#helplocateAccord').collapse('toggle');
}
function drawlocateAccord_clicked(event) {
	$('#drawlocateAccord').collapse('toggle');
}

/**
 * Simulates clicking on a tab in the wizard-container to make it active.
 * @param target of tab to activate. 
 * @example Use '#locate-tab' as param'
 */
function activate_tab(target) {
	var tab = $('.wizard-container ' + target);
	tab.find("a").trigger('click');
	$(window).scrollTop(0);
	return tab;
}

function enable_tab(target) {
	return $(target).removeClass('disabled disabled-tab');
}

function disable_tab(target) {
	return $(target).addClass('disabled disabled-tab ').removeClass('active');
}


/**
 * Checks if sufficient inputs are provided to enable create button
 * This occurs when user clicks Next,
 * Calls pre-checks()
 */
function checkform_next_area(event) {
	"use strict";	
	
	event.preventDefault();
	checkform_next_area.clicked = true;
	
	var validations = pre_checkform_next_area(event);
	var error_count = validations.length; // issues to fix
	if(error_count > 0) {
		var str = "Fix these issues: ";
		for (var p=0; p < error_count ; p++) {
			
			$(validations[p].name).show();
		}
		var msg = 'Fix the issue' + ((error_count  === 1) ? ' ':'s ') + 'above, then click <i>Next</i>.';
		$('#form-errors').html(msg);
	}
	else {
		//set up form for the next stage - get the map location
		$('#form-errors').html(' ');
		$('#next-subform').hide();
		$('#areanameAccord').collapse('hide');
		areanameAccord_setTitle();
		$('#sharingAccord').collapse('hide');
		sharingAccord_setTitle();
		
		$('#monitoringAccord').collapse('hide');
		monitoringAccord_setTitle();
		
		$('#agreementAccord').collapse('hide');
		agreementAccord_setTitle();
		
		$('#helplocateAccord').collapse('show');
		$('#drawlocateAccord_c').collapse('show');
		$('#descriptionAccord').collapse('hide');
		$('#locate-accordion').show();
		$('#map-row').show();
		
		enable_tab("#locate-tab");
		activate_tab("#locate-tab");
		
		initialize_map(null, null);
	}
}
checkform_next_area.clicked = false;

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

/**
 * Called after successful save by save_area(). url is returned from save_area.
 * @param url
 */
function saved_area(url)
{
	"use strict";
	init_area_descriptions(url);

	$('#register-area-legend').hide();

	// make inputs read only
	$('input[type="text"], #area_name').attr('readonly','readonly').parent().find('.help-block').hide();
	$('input[name=opt-sharing]:radio , #new_area_form').attr('disabled', true);
	$('input[name=self-monitor], #new_area_form').attr('disabled', true);
	$('input[name=request-volunteers], #new_area_form').attr('disabled', true);
	$('input[name=accept], #new_area_form').attr('disabled', true);

	// collapse sharing and monitoring and agreement accordions - use can still update them (tbd)
	$('#areanameAccord').collapse('hide');
	areanameAccord_setTitle();
	
	
	$('#sharingAccord').collapse('hide');
	sharingAccord_setTitle();
		
	$('#monitoringAccord').collapse('hide');
	monitoringAccord_setTitle();
	
	$('#agreementAccord').collapse('hide');
	agreementAccord_setTitle();

	// hide next button and ability to change area's location.  
	$('#next-subform').hide();
	$('#helplocateAccord').hide();
	$('#drawlocateAccord_c').hide();
	
	// Display description and boundary form - ask user to enrich info.
	//$("#description-form").show();    
	//$('#descriptionAccord').collapse('show');
	
	
	$("#boundary-row").show();    
	enable_tab("#boundary-tab");
	activate_tab("#boundary-tab");
		
	var selection = $('input[name=opt-fusion]:checked', '#new_area_form').val();
	if((selection === 'is-fusion') || (selection === 'is-drawmap')) {
		//initialize_map(null, null);

		//$('#save_area_id').fadeIn();

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

function initialize_new_area_form() {
	"use strict";
	
	var form_state = 'begin'
		
	var searchBox = addSearchBox();
	$(window).scrollTop(0);
    /* Radio Button Handler - Select Fusion or Draw Map */

	$('#new_area_form input').on('change', pre_checkform_next_area);
	
	$('#next-area').click(checkform_next_area);
	$('#areanameAccord_title').click(areanameAccord_clicked);
	$('#sharingAccord_title').click(sharingAccord_clicked);
	$('#monitoringAccord_title').click(monitoringAccord_clicked);
	$('#agreementAccord_title').click(agreementAccord_clicked);
	$('#descriptionAccord_title').click(descriptionAccord_clicked);
	$('#helplocateAccord_title').click(helplocateAccord_clicked);
	$('#drawlocateAccord_title').click(drawlocateAccord_clicked);
	
	disable_tab("#locate-tab");
	disable_tab("#boundary-tab");
	disable_tab("#description-tab");
	
	
	$('#info-tab').click(function() {
		$(window).scrollTop(0);
	});
	
	$('#locate-tab').click(function() {
		$(window).scrollTop(0);
	});
	
	$('#boundary-tab').click(function() {
		$(window).scrollTop(0);
	});
	
	$('#description-tab').click(function() {
		$(window).scrollTop(0);
	});
	
	var auto_collapse = true;

	$('#auto-collapse').click(function(){

	  if (auto_collapse) { 		//if ($(this).is(':checked')){

		  	//$(this).attr('checked', false);
        	auto_collapse = false;
            $('#inner-descr-accordion .panel-collapse').collapse('show');
            $('#inner-descr-accordion .panel-title').attr('data-toggle', '');
            console.log('Enable accordion behavior');
        } else {
		  	//$(this).attr('checked', true);
        	auto_collapse = true;
            $('#inner-descr-accordion .panel-collapse').collapse('hide');
            $('#inner-descr-accordion .panel-title').attr('data-toggle', 'collapse');
            console.log('Disable accordion behavior');
        }	
	});
	
    $('#inner-descr-accordion').on('show.bs.collapse', function () {
    	if (auto_collapse) $('#inner-descr-accordion .in').collapse('hide');
	});
	

	/* If Testing GeoJson panel*/
	$('#area_name').val('');
}

google.maps.event.addDomListener(window, 'load', initialize_new_area_form);
