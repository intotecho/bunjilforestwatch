/**
 * @name new-area
 * @version 1.0
 * @author Chris Goodman 
 * @copyright (c) 2012-2015 Chris Goodman 
 * @fileoverview Shows a map and allows user to create a new area.
 */

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

/*
 * called when user clicks Create Area.
 * pulls data from the form and validates it. 
 * pulls boundary from the map or fusion table 
 * sends new area request to server.
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
		if (null === map.creator.showData() ) {
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
		//convert (x,y)(x,y) to [x,y], [x,y]  > This coordstring is only printed briefly in the panel, so can be deleted.
		var str = "[" + map.creator.showData(); 
		var n = str.replace(/\(/gi, "[");
		var m = n.replace(/\)\[/gi,   "], [");
		// @fixme
		var coordstring = m.replace(/\)/gi, "]]");
		
		$('#map_panel').append(coordstring);

			//format polygon string returned by showData into an array of mypoints
			var boundaryPoints = [];
			var x = map.creator.showData();
			while(x.length > 1) {
				var nn = x.slice(x.indexOf("(")+1, x.indexOf(")") );
				var mm = nn.split(",");
				x = x.slice(x.indexOf(")")+1);
				var pp = [parseFloat(mm[0]), parseFloat(mm[1])];
				boundaryPoints.push(pp);
			}
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
	
	/* Get the icon, place name, and location.*/
	var image = {
			url: '/static/img/cross-hair-target-col.png', //place.icon
			size: new google.maps.Size(100, 100),
			origin: new google.maps.Point(0, 0),
			anchor: new google.maps.Point(17, 34),
			scaledSize: new google.maps.Size(50, 50)
	};

	// Create a marker for each place.
	var marker = new google.maps.Marker({
		map: map,
		icon: image,
		draggable: true,
		title: place[0].name,
		position: place[0].geometry.location,
		animation: google.maps.Animation.DROP
	});

	map.setCenter(place[0].geometry.location);
	map.setZoom(9);
	
	// remove any points that have been draw.
	map.creator.destroy();
	map.creator=new PolygonCreator(map);
}


/**
 *Listen for the event fired when the user selects an item from the
	   pick list. Retrieve the matching places for that item. 
	   Although this supports multiple markers we only get one which is good. 
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
function geolocate_region(accuracy) {
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
			return circle.getBounds();
		});
	}
	return null
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
	var users_region = geolocate_region(1000);
	if (users_region !== null) {
		searchBox.setBounds(users_region);
	}
    
	// When the user selects an address from the dropdown, call searchPlaceSelected
	
	searchBox.addListener('places_changed', function() {
	    searchPlaceSelected(map, searchBox);
	});

	return searchBox;
}
	

/**
 * initialize_map.initialized  ensures it may be called repetedly.
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
	};
	var map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);
	
	initialize_map.map = map;
	
	/* global PolygonCreator */     
	map.creator = new PolygonCreator(map);       

	/*function to add the polygon coordinates to the form data prior to submit.*/ 
	$('#createarea_id').click(function(){ 
		createArea(map);
	});		

	//Oops! Redraw
	$('#reset_id').click(function(){ 
		map.creator.destroy();
		map.creator=new PolygonCreator(map);
	});		 

	//show paths
	$('#showData').click(function(){ 
		console.log("map-panel draw");
		$('#map_panel').empty();
		if(null === map.creator.showData()){
			$('#map_panel').append('Please mark out your area first, then click Create Area');
		}
		else {
			$('#map_panel').append(map.creator.showData());
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
				//removeLandsatGrid();
			}
		}
	});

	google.maps.event.addListener(map, 'bounds_changed', function() {
		/*  var bounds = map.getBounds();
			searchBox.setBounds(bounds);*/
		if (map.getZoom() > 6) {
			console.log ("Show Landsat Grid");
			createLandsatGridOverlay(map, 0.5, false, null);
		}
	});

	google.maps.event.addListener(map, 'idle', function() {
		//This is needed so the fusion tables query works
		var map_center = map.getCenter();
		if (map_center.lng() < -180) { 
			map.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng()+360));
		}
		if (map_center.lng() > 180) { 
			map.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng() - 360));
		}	
	});


	if (place !== null){
		zoomToPlace(map, place);
	}
	return map;
}
initialize_map.map = null;


/**
 * Initialises the form for new-area page, but not yet the map.
 */
function initialize_new() {
	"use strict";

	var searchBox = addSearchBox();
    
    /* Radio Button Handler - Select Fusion or Draw Map */
	
	$('#new_area_form input').on('change', function() {
		var selection = $('input[name=opt-fusion]:checked', '#new_area_form').val();
		console.log("selected: ", selection);
		//$('#new-map-control-panel').removeClass('col-md-9').addClass('col-md-3');
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
	});
	
	/** -- resize the map div - This uses a tip from //github.com/twitter/bootstrap/issues/2475 --> */
	$(window).resize(function () {
		var h = $(window).height();
		var offsetTop = 60; // Calculate the top offset
		$('#map-canvas').css('height', (h - offsetTop));	        
	}).resize();   

}

google.maps.event.addDomListener(window, 'load', initialize_new);
