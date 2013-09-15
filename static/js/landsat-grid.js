/*******************************************************************************
Copyright (c) 2013 Chris Goodman
Creative Commons License to share
******************************************************************************/

var LANDSAT_GRID_FT = '1kSWksPYW7NM6QsC_wnCuuXO7giU-5ycxJb2EUt8';//https://www.google.com/fusiontables/DataSource?docid=1kSWksPYW7NM6QsC_wnCuuXO7giU-5ycxJb2EUt8
var COUNTRY_GRID_FT = '1foc3xO9DyfSIF6ofvN0kp2bxSfSeKog5FbdWdQ'; //https://www.google.com/fusiontables/data?docid=1foc3xO9DyfSIF6ofvN0kp2bxSfSeKog5FbdWdQ
var BUNJIL_API_KEY = 'AIzaSyDxcijg13r2SNlryEcmi_XXxZ9sO4rpr8I' //https://code.google.com/apis/console/
var landsat_overlays = [];

var gridInitialised;


infoWindowArray = [];

function resetInfoWindow(){
    if(infoWindowArray){
        for(i in infoWindowArray){
            infoWindowArray[i].close();
        }
    }
}

function requestLandsatGrid(map, showlayer)
{
	// Initialize JSONP request for LANSAT grid Fusion Table
	// Based on https://developers.google.com/fusiontables/docs/samples/mouseover_map_styles
	if(gridInitialised != true) {
		if (showlayer == true)
		{
			gridInitialised = true;
		    var map_center = map.getCenter(); //new google.maps.LatLng({{area.map_center}});
		    var map_distance = google.maps.geometry.spherical.computeDistanceBetween(map.getBounds().getNorthEast(), map.getBounds().getSouthWest());
		    var radius = 150000; // how far away to show cells from a small AOI in metres
		    var distance = (map_distance > radius)? map_distance : radius;  //but fill the view area
		    distance = (distance> 1000000)? 2000000 : distance; //unless the view area is more than 2000km.
		    
		    console.log(radius, map_distance, distance);
		    
		    var script = document.createElement('script');
		    var url = ['https://www.googleapis.com/fusiontables/v1/query?'];
		    url.push('sql=');
		    var query = 'SELECT name, geometry, description FROM ' + LANDSAT_GRID_FT + ' WHERE ST_INTERSECTS(geometry, CIRCLE(LATLNG' + map_center + ' , ' + distance + ' ))';
			console.log("ft query: ", query);
		    var encodedQuery = encodeURIComponent(query);
		    url.push(encodedQuery);
		    url.push('&callback=drawLandsatGrid');
		    url.push('&key='+ BUNJIL_API_KEY);
		    script.src = url.join('');
		    var body = document.getElementsByTagName('body')[0];
		    body.appendChild(script);
	    }
	}
	else
	{
		if (showlayer == false )
		{
		 	console.log("deleting landsat layer script");
		 	resetInfoWindow();
			gridInitialised = false;
			//var body = document.getElementsByTagName('body')[0];
			var script = document.getElementById('script');
			if(script) {
				script.parentElement.removeChild(script); //script is undefined. this is not working.
			}
		}
	}
}


function removeLandsatGrid() {
	while (landsat_overlays.length > 0)
	{
		var landsat_cell = landsat_overlays.pop();
		landsat_cell.setVisible(false);
		landsat_cell.setMap(null);
	}
}

function drawLandsatGrid(data) {
	var rows = data['rows'];
    //var currentBounds = map.getBounds(); // get bounds of the map object's current (initial) viewport
    for (var i in rows) {
		var infoWindow = new google.maps.InfoWindow();
		infoWindowArray.push(infoWindow);
		
		//console.log(data);
    	var newCoordinates = [];
        var geometry = rows[i][1]['geometry']
        if (geometry) {
			newCoordinates = constructNewCoordinates(geometry);
			var description = rows[i][2];
			var landsat_cell = new google.maps.Polygon({
        	paths: newCoordinates,
        	strokeColor: '#FFFFFF',
        	strokeOpacity: 0.4,
        	strokeWeight: 1,
        	fillOpacity: 0,
        	suppressInfoWindows: true,
        	content: description
	        });
			landsat_cell.set("Description", description);  // Add attributes for adding description into polygon.   
	        
			landsat_overlays.push(landsat_cell);
			
			google.maps.event.addListener(landsat_cell, 'mouseover', function(e) {
	            this.setOptions({fillOpacity: 0.3, strokeWeight: 5});
	        });
	        google.maps.event.addListener(landsat_cell, 'mouseout', function(e) {
	            this.setOptions({fillOpacity: 0, strokeWeight: 1});
	        });
	       	google.maps.event.addListener(landsat_cell, 'zoom', function(e) { //needs work
	         	if (e.zoom() < 6) {landsat_cell.hidden();}
	         	else {landsat_cell.show();}
	         	console.log(e.zoom());
	       	});
	       	
 			google.maps.event.addListener(landsat_cell, 'click', function(e) {
 				resetInfoWindow();
 				infoWindow.setOptions({
 			   		content: this.get("Description"),  		
 			   		position: e.latLng,
 			   		pixelOffset: e.pixelOffset,
 			 	});
 				infoWindow.open(map);
  			});
 			
        	landsat_cell.setMap(map);
  		} // if geometry 
  		else {
				console.log("no geometry ", i);
		}
 	} //each row
    console.log(landsat_overlays);
	
  }//drawLandsatGrid

function constructNewCoordinates(polygon) {
	var newCoordinates = [];
    var coordinates = polygon['coordinates'][0];
    for (var i in coordinates) {
      newCoordinates.push(
          new google.maps.LatLng(coordinates[i][1], coordinates[i][0]));
    }
    return newCoordinates;
}

// function GetPolygonBounds(poly ) {
//No longer called because intersection filter is done in the server, not browser.
//	var bounds = new google.maps.LatLngBounds();
//	var paths = poly.getPaths();
//	var path;
//	for (var p = 0; p < paths.getLength(); p++) {
//	        path = paths.getAt(p);
//	        for (var i = 0; i < path.getLength(); i++) {
//	                bounds.extend(path.getAt(i));
//	        }
//	}
//	return bounds;
//}

