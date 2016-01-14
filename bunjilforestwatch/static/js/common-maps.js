// functions used by both base-maps and new-area - unlike site.js, this requires googlemaps api.
/**
 * Modify area with new value defined in the patch_ops.
 * http://williamdurand.fr/2014/02/14/please-do-not-patch-like-an-idiot/  
 */
function patch_area(patch_ops, area_url)
{
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


var areaBoundaryPolygonOptions = {
  
    strokeColor: '#FFFF00',
    strokeOpacity: 0.5,
    strokeWeight: 2,
    fillColor: '#000000',
    fillOpacity: 0.05
};

/**
 * Functions common to both new-area and base-maps
 */

/**
 * @returns a polygonOptions that can be added to a map.
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

function save_view(map, area_json) {

	if (typeof map === 'undefined') {
		console.log("Save_view() no map");	
		return;
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
		//activate_tab("#descr-tab");
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
 * clone area_json object but only take clean geojson suitable for googlemaps
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
 * @returns returns the area_area in the input text control.
 */
function get_area_name() {
	var area_name = $('#area_name').val();
	if (typeof (area_name) === 'undefined') {
		area_name = '';
	}
	// console.log('area_name: ', area_name);
	return area_name;
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


