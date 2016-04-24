/**
 * Functions common to both new-area and base-maps.
 * unlike site.js, this requires googlemaps api.
 */

/**
 * @returns: a promise. 
 * Modify area with new value defined in the patch_ops.
 * @see: [williamdurand.fr/2014/02/14/please-do-not-patch-like-an-idiot/] for usage.  
 */
function patch_area(patch_ops, area_url)
{
	"use strict";
	var patch_ops_string = JSON.stringify(patch_ops);

	//console.log( "updateAreaDescription() url:", area_json.properties.area_url, ' data:', patch_ops_string);
  
	return jQuery.ajax({
	    type: "POST",
	    beforeSend: function (request)
        {
            request.setRequestHeader("X-HTTP-Method-Override", "PATCH");
        },
	    url: area_url, //area_json.properties.area_url,
	    data: patch_ops_string,
	    dataType:"json"
	});
}

/**
 * @global: map_options consistent map display controls
 */
var map_options = {
		/* global google */
        mapTypeId: google.maps.MapTypeId.TERRAIN,
        panControl:true,
        zoomControl:true,
		zoomControlOptions : {
			position : google.maps.ControlPosition.LEFT_TOP
		},
        mapTypeControl:true,
		mapTypeControlOptions : {
			style : google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
			position : google.maps.ControlPosition.TOP_RIGHT
		},
        streetViewControl:false,
        overviewMapControl:false,
        rotateControl:false,
        clickable: true,
        scaleControl: true,
        scaleControlOptions: {position: google.maps.ControlPosition.BOTTOM_RIGHT},
		drawingControl : false
    };

/**allow or prevent user to zoom and pan the map 
 * @param lock: true of false.
 * useful when drawing finished.
 * @param map. adds a attribute 'is_mapOptions' to map.
 */
function lock_map(map, lock) {
	var mapOptions = {};
	if(lock === true) {
		mapOptions = {
			    zoomControl: false,
			    scrollwheel: false,
			    navigationControl: false,
			    draggable: false,
			    disableDoubleClickZoom: true
		};
		map.is_locked = true;
	}
	else {
		mapOptions = {
			    zoomControl: true,
			    scrollwheel: true,
			    navigationControl: true,
			    draggable: true,
			    disableDoubleClickZoom: false
		};
		map.is_locked = false;
	}
	return map.setOptions(mapOptions);
}

/**
 * prevent user from moving the map
 * useful when drawing. Does not change the UX button states.
 * @param map
 */
/*
function is_map_mapOptions(map) {

	var mapOptions = {
	    zoomControl: false,
	    scrollwheel: false,
	    navigationControl: false,
	    draggable: false,
	    disableDoubleClickZoom: true,
	};
	return map.setOptions(mapOptions);
}
*/


var areaBoundaryPolygonOptions = {
    strokeColor: '#FFFF00',
    strokeOpacity: 0.5,
    strokeWeight: 2,
    fillColor: '#000000',
    fillOpacity: 0.05
};


/**
 * @returns: a polygonOptions that can be added to a map.
 * @usage: var polygon = new google.maps.Polygon(boundaryPolygonOptions(area_json));
 * 	      map.setMap(polygon);
 */
function boundaryPolygonOptions(input_geosjon) {
	
	var boundary_feature;
	
	if (input_geosjon.type === "FeatureCollection"){
		boundary_feature = get_area_feature(area_json, "boundary");
	}
	else if (input_geosjon.type === "Feature"){
		boundary_feature = input_geosjon;
	}
	else {
		console.log("boundaryPolygonOptions() - no geometry");
	}
	
    var coords_arr   =  boundary_feature.geometry.coordinates[0];
    var border_latlngs = [];
    var polygonOptions = areaBoundaryPolygonOptions;

    for (var j=0; j < coords_arr.length; j++)
    {
        latlng = new google.maps.LatLng(coords_arr[j][1], coords_arr[j][0] );
        //console.logprint parseInt(coords_arr[j].lat. parseInt(coords_arr[j].lng
        border_latlngs.push(latlng);
    }

    /* global areaBoundaryPolygonOptions */  
    polygonOptions.paths = border_latlngs;
    return polygonOptions;
}

/*
 * updates the zoom and pan of the map view.
 */
function save_view(map, area_json) {

	if (typeof map === 'undefined') {
		console.log("Save_view() no map");	
		return null;
	}
		
	var url =  area_json.properties.area_url;

	value = {
	        "type" : "Feature",
	        "geometry" : {
	            "type" : "Point",
	            "coordinates" : [ map.getCenter().lng().toFixed(5), map.getCenter().lat().toFixed(5)]
	        },
	        "properties" : {
	            "name" : "mapview",
	            "zoom" : map.getZoom()
	        }
	    };   

	$('#save-boundary-popover').popoverX({
		target : '#save-view' // container
	});

	$('#save-boundary-popover').popoverX('show');
	
	var patch_ops =  [];
	patch_ops.push( { "op": "replace", "path": "/features/mapview", "value": value});

	var request = patch_area(patch_ops, area_json.properties.area_url);  //patch_area(); //ajax call

    request.done(function (data) {
    	if(typeof data !== 'undefined') {
    		console.log ('patch_area() - result: ' + data.status + ', ' + data.updates.length + ' updates: ' + data.updates[0].result);
    	}
    	var msg = 'Area ' + get_area_name() + ' updated view'
    	$('#save-boundary-popover').popoverX('hide');
		addToasterMessage(msg);
		console.log(msg);
    });
    
    request.fail(function (xhr, textStatus, error) {
    	var msg = 'Error ' + xhr.status + ' ' +
		xhr.statusText + ' ' +
		xhr.responseText;
		console.log ('patch_area() - failed:', xhr.status,  ', ', xhr.statusText, ' error: ', error);
    });
    return request;
}

/**
 * return the feature matching the featureName
 * @param featureName: - the name of a feature
 * @returns: a feature if found, else null.
 */

function get_area_feature(area_json, featureName) {
	for (var i=0; i < area_json.features.length; i++) {
		if (area_json.features[i].properties.name === featureName) {
			return area_json.features[i];
		}
	}
	return null;
}

/**
 * hasFeature returns the the first feature found with geometry of the requested featureType.
 * Used to see if the FeatureCollection contains a boundary or just points.
 * @param geojson: Must be a FeatureCollection.
 * @param featureType: string, expected to be one of the GeoJson allowed types such as "Polygon' or "Point"
 * @returns: null if not found, otherwise the first matching feature found.
 * @example: map.data.toGeoJson(function(geojson) { if (f=hasFeature(geojson, "Polygon") !== null) {...boundary exists...} }
 */
function hasFeature(geojson, featureType) {
	"use strict";
	if (geojson.type != 'FeatureCollection') {
		return null;
	}
	for (var i=0; i < geojson.features.length; i++) {
		if (geojson.features[i].type === 'Feature') {
			if (geojson.features[i].geometry.type === featureType) {
				return geojson.features[i];
			}
		}
	}
	return null;
}

/**
 * clone area_json object but only take clean geojson suitable for googlemaps.
 * removes any unexpected styling
 * @param: area_json a featureCollection
 * @returns: a featureCollection
 */
function get_clean_geojson(area_json) {
	var new_area_json = {
			"properties" :  area_json.properties,
			"type": "FeatureCollection",
			  "features": [
			  ]
	};
	var boundary = get_area_feature(area_json, "boundary"); 
	if (boundary !== null) 
	{
		new_area_json.features.push(boundary);
	}
	else {
		var location = get_area_feature(area_json, "area_location"); 
		if (location !== null) 
		{
			new_area_json.features.push(location);
		}
	}
	return new_area_json;
}



/**
 * @returns a google.map.LatLng to center a map based on the mapview 
 * @param area_json
 */
function center_mapview(area_json) {
	var mapview = get_area_feature(area_json, "mapview");
	if (mapview !== null) {
		var center_coords = mapview.geometry.coordinates;  // init global.
	    return new google.maps.LatLng(center_coords[1], center_coords[0] );
	}
	console.log("center_mapview(): error no mapview stored;");
    return new google.maps.LatLng(0, 0);
}

/**
 * @returns a zoom level based on the mapview 
 * @param area_json
 */
function zoom_mapview(area_json) {
	var mapview = get_area_feature(area_json, "mapview");

	if (mapview !== null) {
		return mapview.properties.zoom;
	}
	console.log("zoom_mapview(): error no mapview stored;");
	return 7;
}

/**
 * 
 */
/**
 * Collect the Boundary coordinates from the area and convert to a Google Maps object.
 * @TODO: Border of AOI does not adjust opacity on both overlays yet.
*/
function displayBoundaryHull(map) {

	var boundary_feature = get_area_feature(area_json, "boundary_hull");
	
    if ((boundary_feature === null) || (boundary_feature.geometry.coordinates[0].length === 0))
    {
    	var latlng = areaLocation(area_json);
    	if (latlng === null) {
    		latlng = map.getCenter();
    	}
		var marker = new google.maps.Marker({
				position: latlng,
				title: area_json.properties.area_name 
		});
    	// add the marker to the maps
    	marker.setMap(map);
    	marker.name = 'location';
    	marker.overlaytype = 'drawing';
    	return marker;
    }
    else {
	    var coords_arr   =  boundary_feature.geometry.coordinates[0];  // init global.
	    var border_latlngs = [];
		
	    if (coords_arr.length === 0 ) {   
	    	return null;
	    }
	    else {
	    	
		    var polygonOptions = boundaryPolygonOptions(boundary_feature);
		    
			var areaBoundary = new google.maps.Polygon(polygonOptions); //areaBoundaryPolygonOptions defined in site.js
		    areaBoundary.name = "boundary hull";
		    areaBoundary.overlaytype = 'drawing';
		    areaBoundary.setMap(map);
		    return areaBoundary;
		    
	    }    
    }
}


/**
 * Make the data layer editible or not base on the parameter.
 * @returns a data layer, or null.
 */
function makeDataLayerEditable(data, editable) {
    try {
    	var styleOptions = areaBoundaryPolygonOptions;
    	if (editable) {
    		styleOptions.editable = true;
    		styleOptions.draggable = true;
    		styleOptions.fillOpacity =  0.5;  //more opacity when drawing.
        	styleOptions.strokeColor =  'yellow';  
        	styleOptions.fillColor =  'yellow'; 
    	}
    	else {
    		styleOptions.editable = false;
    		styleOptions.draggable = false;
    		
    		styleOptions.fillOpacity =  0.2;  
        	styleOptions.strokeColor =  'green';  
        	styleOptions.fillColor =  'gray'; 
    	}	
    	
    	data.setStyle(styleOptions);
    
    	
    } catch(e){
    	var msg = 'makeDataLayerEditable exception: ' + e;
    	console.log(msg);
    	return null;
    }
}

/**
 * Draw the boundary provided by user as a google.map.data layer.
 * @TODO: Data Layers don't adjust opacity on both overlays yet.
 * @returns a data layer, or null.
 */
function createDataLayer(map, editable) {
    try {
  
       	//makeDataLayerEditable(map.data, editable);
    	
    	var newData = new google.maps.Data({
    		map : map,
    		style : map.data.getStyle(),
    		controls : null,
    		drawingMode: null
    	});

    	newData.setOptions({
    		drawingControl: false,
    		drawingMode: null,
    		controls : null,
    		position: google.maps.ControlPosition.TOP_CENTER,
    	});
    	makeDataLayerEditable(newData, editable);
        return newData;

    } catch(e){
    	var msg = 'createDataLayer exception: ' + e;
    	console.log(msg);
    	return null;
    }
}



/**
 * Draws the featureCollection on map with a data layer
 * @param map: a google map with a data layer.
 * @param geojson: A FeatureCollection
 * @returns: The imported features are returned or null if maps throws an exception if the GeoJSON could not be imported.
 */
function displayFeatureCollection(map, geojson) {
    try {
    	if (typeof map.data === 'undefined') {
    		console.log('displayFeatureCollection requires data layer ');
    		return;
    	}
    	if (geojson.type != 'FeatureCollection') { /* other types Feature and Geometry could be allowed */
    		return null;
    	}
    	var length = geojson.type;
    	if (length === 0) {
    		return null;
    	}
    	
    	try {
    		return map.data.addGeoJson(geojson);
    	} catch (error) {
    		console.log("could not add geojson to map: " + error.message);
    		return null;
    	}    		    
    } catch(e) {
    	console.log('displayFeatureCollection could not add Feature Collection : ' + e + ', geojson: ' + geojson);
    	return null;
    }
}

var loss_types =
[
	'mechanical', 'harvesting', 'fire', 'disease', 'storm'
];
