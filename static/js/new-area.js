/**
 * @name new-area
 * @version 1.0
 * @author Chris Goodman 
 * @copyright (c) 2012-2015 Chris Goodman 
 * @fileoverview Shows a map and allows user to create a new area.
 */

var map;
var map_initialised = false

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
        

function initialize_map() {
	"use strict";

	var center = $('#latlng').text(); //TODO: Refactor using area_json
	//NOT USED user_url    = $('#user_url').text();
	var  arr = center.split(',');
	
  var mapOptions = {
 	    center: new google.maps.LatLng(arr[0], arr[1]),
 	    overviewMapControl: true,
 	    zoom: 3,
 	    mapTypeId: google.maps.MapTypeId.HYBRID
  };
  
  /* @fixme map should not be global*/    
  map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);
  /* global PolygonCreator */     
  var creator = new PolygonCreator(map);       

  /*function to add the polygon coordinates to the form data prior to submit.*/ 
      
  $('#createarea_id').click(function() { 
  	var problems = "";
  	var area_name =  $('#area_name').val();
    var area_descr =  $('#area_descr').val();
    var area_boundary_ft =  $('#boundary_ft').val();
      
    var selection = $('input[name=opt-fusion]:checked', '#new_area_form').val();
      
      // form validation
    if ((null === area_name) || (area_name === "")) {
      problems += 'Please give your area a short name<br/><br/>';
    }
  	/* 
    else [ 
    	if(!/^[a-zA-Z 0-9]+$/.test(area_name))[
        	problems += 'Sorry, Please use only the characters A-Z, a-z and 0-9 in the area name. A full name can be entered into the description\n\n';
    	]
    ]
  	*/
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
      if (null === creator.showData() ) {
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
       var str = "[" + creator.showData(); 
       var n = str.replace(/\(/gi, "[");
       var m = n.replace(/\)\[/gi,   "], [");
       var coordstring = m.replace(/\)/gi, "]]");
       $('#map_panel').append(coordstring);
                                           
       //format polygon string returned by showData into an array of mypoints
       var boundaryPoints = [];
       var x = creator.showData();
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
    document.getElementById("coordinates_id").value = toServer
    $("#new_area_form").submit();
            
  }); /* end-of-createarea_id.click() */       


  //Oops! Redraw
	$('#reset_id').click(function(){ 
	 		creator.destroy();
	 		creator=null;
	 		creator=new PolygonCreator(map);
	});		 

	//show paths
	$('#showData').click(function(){ 
    console.log("map-panel draw");
 		$('#map_panel').empty();
 		if(null === creator.showData()){
 			$('#map_panel').append('Please mark out your area first, then click Create Area');
 		}
    else {
 			$('#map_panel').append(creator.showData());
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
	
	/** --resize div tip from //github.com/twitter/bootstrap/issues/2475 --> */
	$(window).resize(function () {
	  "use strict";
	  var h = $(window).height();
	  var offsetTop = 60; // Calculate the top offset
	  $('#map-canvas').css('height', (h - offsetTop));	        
	}).resize();   
	
	/* Create the search box and link it to the UI element. */
	var markers = [];
	var input = /** @type {HTMLInputElement} */(
	    document.getElementById('searchbox_id'));
	
	map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
	var searchBox = new google.maps.places.SearchBox(
	    /** @type {HTMLInputElement} */(input));
	
	  /** Listen for the event fired when the user selects an item from the
	   pick list. Retrieve the matching places for that item. */
	google.maps.event.addListener(searchBox, 'places_changed', function() {
	  "use strict";
	
	  var places = searchBox.getPlaces();
	  var len = places.length 
	  if (len === 0) {
	    return;
	  }
	          
	  /* @fixme This does not look right!!!!
	  for (var j = 0, marker; marker = markers[j]; j++) {
	    marker.setMap(null);
	  }
	  */
	  
	  /* For each place, get the icon, place name, and location.*/
	  var markers = [];
	  var bounds = new google.maps.LatLngBounds();
	  for (var i = 0; i < len; i++) {
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
	      title: places[i].name,
	      position: places[i].geometry.location,
	      animation: google.maps.Animation.DROP
	    });
	          	
	  	markers.push(marker);
	
	    map.setCenter(places[i].geometry.location);
	    map.setZoom(9);
	  } /*end-for*/
	      
	});
	    
	google.maps.event.addListener(map, 'bounds_changed', function() {
		  "use strict";
	
		    var bounds = map.getBounds();
		    searchBox.setBounds(bounds);
		    if (map.getZoom() > 6) {
	  	   console.log ("Show Landsat Grid");
	         createLandsatGridOverlay(map, 0.5, false, null);
	      }
		  /* else {
	          //createLandsatGridOverlay(map, 0, true, null);
	          //removeLandsatGrid();
		   } */ 
	});
	  
	google.maps.event.addListener(map, 'idle', function() {
		  "use strict";
	
		//This is needed so the fusion tables query works
	      var map_center = map.getCenter();
	      if (map_center.lng() < -180) { 
	          map.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng()+360));
	      }
	      if (map_center.lng() > 180) { 
	          map.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng() - 360));
	      }
	});

}

function initialize_new() {
	"use strict";
	
  /*Radio Button Handler - Select Fusion or Draw Map */
	$('#new_area_form input').on('change', function() {
    var selection = $('input[name=opt-fusion]:checked', '#new_area_form').val();
    console.log("selected: ", selection);
 
    if((selection === 'is-fusion') ||(selection === 'is-drawmap')) {
      if (map_initialised === false) {
          initialize_map();
          $('#searchbox_id').fadeIn(); 
          map_initialised = true;
      }
  
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
}

google.maps.event.addDomListener(window, 'load', initialize_new);
  