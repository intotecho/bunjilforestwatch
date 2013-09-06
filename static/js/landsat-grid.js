/*******************************************************************************
Copyright (c) 2013 Chris Goodman
Creative Commons License to share
******************************************************************************/

var LANDSAT_GRID_FT = '1kSWksPYW7NM6QsC_wnCuuXO7giU-5ycxJb2EUt8';//https://www.google.com/fusiontables/DataSource?docid=1kSWksPYW7NM6QsC_wnCuuXO7giU-5ycxJb2EUt8
var COUNTRY_GRID_FT = '1foc3xO9DyfSIF6ofvN0kp2bxSfSeKog5FbdWdQ'; //https://www.google.com/fusiontables/data?docid=1foc3xO9DyfSIF6ofvN0kp2bxSfSeKog5FbdWdQ
var BUNJIL_API_KEY = 'AIzaSyDxcijg13r2SNlryEcmi_XXxZ9sO4rpr8I' //https://code.google.com/apis/console/

	
function drawLandsatGrid(data) {
	var rows = data['rows'];
    //var currentBounds = map.getBounds(); // get bounds of the map object's current (initial) viewport
       
    for (var i in rows) {
		var infoWindow = new google.maps.InfoWindow();
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

			//landsat_cell.description = description;
			
			//landsat_cell.infoWindow = new google.maps.InfoWindow(
    		//{ 
        	//	content: description
    		//});
 			//console.log('infoWindow:', description, landsat_cell.infoWindow, rows[i][2]);
 
	        //below query was moved to the fusion table server
	        //cell_bounds = GetPolygonBounds(landsat_cell);
	        //if (cell_bounds.intersects(currentBounds))
	        {
	        	// if any point of cell is in view, add to map.
	        	//console.log("visible");
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
     				
     				infoWindow.setOptions({
     			   		content: this.get("Description"),  		
     			   		position: e.latLng,
     			   		pixelOffset: e.pixelOffset,
     			 	});
     				infoWindow.open(map);
      			});

	        	landsat_cell.setMap(map);
			}
  		} // if geometry 
  		else {
				console.log("no geometry ", i);
		}
 	} //each row
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
//No longer called because intersection filter is done in the server
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

