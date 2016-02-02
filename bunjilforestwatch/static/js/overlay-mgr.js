
/*******************************************************************************
 * Copyright (c) 2014 Chris Goodman GPLv2 Creative Commons License
 * See also https://developers.google.com/maps/documentation/javascript/examples/overlay-hideshow
 ******************************************************************************/

var overlayMaps = [];
var jobs = [];
var numjobs = 0;

// Keep track of pending tile requests - after http://stackoverflow.com/questions/7341769/google-maps-v3-how-to-tell-when-an-imagemaptype-overlays-tiles-are-finished-lo?rq=1
var pendingUrls = [];
var maxPendingUrls = 0;

/**
 * returns a new map.landsatGridOverlay based on the cellarray 
 * does not create a new overlay if map already  has one. (see deleteLandsatGridOverlay)
 */
function createLandsatGridOverlay(map, opacity, clickable, cellarray, layer_id) { 
	"use strict";
    if ((typeof map.landsatGridOverlay === 'undefined') || (map.landsatGridOverlay === null)){
        var landsatGridOverlay = new LandsatGridOverlay(map, opacity, clickable, cellarray);
        landsatGridOverlay.name = layer_id;
        landsatGridOverlay.overlaytype = 'drawing';

        landsatGridOverlay.initialize();       
        map.landsatGridOverlay = landsatGridOverlay;
        overlayMaps.push(landsatGridOverlay);
        update_cell_panel(landsatGridOverlay);
    }
    return map.landsatGridOverlay;
}

function deleteLandsatGridOverlay(map, opacity, clickable, cellarray) { 
	"use strict";
    if ((typeof map.landsatGridOverlay !== 'undefined') && (map.landsatGridOverlay !== null)){
        var id;
		do {
			id = findOverlayLayer(map.landsatGridOverlay.name, overlayMaps);
			if (id !== -1) {
				console.log("removing landsat grid :" + overlayMaps[id].name);
				deleteLandsatGrid(map.landsatGridOverlay);
				overlayMaps.splice(id, 1);
			}
		} while (id !== -1);

		delete map.landsatGridOverlay;//delete the overlay
		map.landsatGridOverlay = null;
    }
}
 
//find overlay in obs matching role and viz algorithm.
function findOverlay(obs, role, algorithm) {
	"use strict";
    for (var o = 0; o < obs.overlays.length; o++) {
        var overlay = obs.overlays[o];
        if ((overlay.overlay_role == role) && (overlay.algorithm == algorithm)) {
        	return overlay;
        }         
    }
    return null;
}

function requestAdHocOverlay() { //not assoc with a task...
	"use strict";
 	var httpget_url = httpgetActionUrl("overlay");
    console.log( "urls", httpget_url);
 	var overlayname = "AdHoc overlay";
    var tooltip = "AdHoc overlay - " + httpget_url;
	
    fetchOverlay(overlayname, tooltip, "<small>Creating new AdHoc overlay</small>", httpget_url );
}


function fetchOverlay(overlayname, tooltip, prompt, httpget_url) {	
	"use strict";
	  
	  prompt += ' <img src="/static/img/ajax-loader.gif" class="ajax-loader"/>';
      
	  var jobid = addJob(prompt, 'green');
      
      $.get(httpget_url).done(function(data) {
    	  if(data === "") {
    	   		updateJob(jobid, "<p class = 'small'>" + "no data from server"+"</p><br>", 'red');
    	  }
    	  else {
	    	  var ovl = jQuery.parseJSON(data);
		       if (ovl) {
			       if (ovl.result == 'error') {
		    	   		updateJob(jobid, "<p class = 'small'>" + ovl.reason +"</p><br>", 'red');
			    	   }
			       else {
			    	   displayOverlay(ovl, overlayname, tooltip);
			    	   removeJob(jobid);
			       }
		       }
		       else {
		    	   		updateJob(jobid, "<p class = 'small'>No Overlay Data</p><br>", 'red');
		       }
    	   }
	  }).error(function( jqxhr, textStatus, error ) {
	           var err = textStatus + ', ' + error;
	           console.log( "Request " + jobid + " Failed: " + err);
	           updateJob(jobid, "<p class='small'>Failed: " + err + "</p><br>", 'red');
	  });
}

function updateOverlay(ovl, overlayname, tooltip) {
	"use strict";
    
	var prompt  = "Updating " + ovl.overlay_role + " "  + ovl.algorithm;

	var httpget_url = 'overlay/update/' + ovl.key + '/' + ovl.algorithm; 
    
    console.log( "updateOverlay() %s as: %s", prompt, httpget_url);
    
    fetchOverlay(overlayname, tooltip, '<small>' + prompt + '</small>', httpget_url );
}

function createObsOverlay(obs, role, algorithm) {
	"use strict";
	var httpget_url = 'overlay/create/'  + obs.encoded_key + '/' + role + '/' + algorithm; 
	
	var prompt  = "Creating " + role + " "  + algorithm + " overlay";
       
    console.log( "createObsOverlay() %s as: %s", prompt, httpget_url);
    
    var overlayname = obs.captured;          
    var tooltip = "Overlay: " +  overlayname + " " + role  + " " +  algorithm + " Image: " + obs.image_id ;
    
    fetchOverlay(overlayname, tooltip, '<small>' + prompt + '</small>', httpget_url);
}


function displayObsOverlay(obs, role, algorithm) { //called from base-maps.html
	"use strict";
    var ovl = findOverlay(obs, role, algorithm);
    
    if (ovl !== null) {
    	
    	var test_tile_url = ['https://earthengine.googleapis.com/map', ovl.map_id, 1, 0, 0].join("/");
    	test_tile_url += '?token=' + ovl.token;

    	var tooltip = "Overlay: " +  obs.captured  +  " Id: " + obs.image_id + " " + ovl.overlay_role + " " + ovl.algorithm;
        var overlayname = obs.captured + ":" + ovl.overlay_role;          

    	$.get(test_tile_url).done(function(data) {
    	       console.log("Map overlay already generated");
               displayOverlay(ovl, overlayname, tooltip);
    	      
        }).error(function( jqxhr, textStatus, error ) {
                console.log("Map overlay expired - regenerating");
                updateOverlay(ovl, overlayname, tooltip);
        });
    }
    else {
        createObsOverlay(obs, role, algorithm);
    }
}
	
function displayOverlay(ovl, overlayname, tooltip) { //overlay is current so add it to the map.
	"use strict";
    if (ovl.overlay_role == 'latest') 
    	createImageOverlay("show", map_over_lhs, ovl.map_id,  ovl.token, overlayname, tooltip, 'red');
    else if (ovl.overlay_role == 'prior') {	
      	createImageOverlay("show",  map_rhs,        ovl.map_id,  ovl.token, overlayname, tooltip,  'green'  );
    	createImageOverlay("wipe",   map_under_lhs, ovl.map_id,  ovl.token, overlayname, tooltip,  'brown'  );
    }
    else 
    	createImageOverlay("show", map_over_lhs, ovl.map_id,  ovl.token, overlayname, tooltip, 'blue');
}
 

function layerslider_callback(layer_id, val) {
	"use strict";
    console.log("layerslider_callback : " + layer_id + ", " + val);
    
    var id = findOverlayLayer(layer_id, overlayMaps);
    if (id !== -1) {
        console.log("layerslider_callback:" + overlayMaps[id].name + ", " + val); //overlayMaps[id].name
        console.log('type of overlay' + typeof overlayMaps[id]); 
        if(overlayMaps[id].name == 'boundary') { //TODO: Too brittle. Need better way to determine objct type.
        	 overlayMaps[id].setOptions({strokeOpacity :val/100} );	 
        }
        else {
        	console.log('type' + typeof overlayMaps[id]);
        	if (overlayMaps[id].overlaytype !== 'datalayer') {
        		overlayMaps[id].setOpacity(Number(val)/100);
        	}
        	else {
            	console.log("can't fade data layer");
        	}
        		
        }
    }
}

function createImageOverlay(operation, google_map, map_id,  token, overlay_name, tooltip, color)
{
	"use strict";

    if((operation == 'show')||(operation == 'wipe'))
    {
    	//truncate string to chars before the '@', or max 30 if no '@'
    	var idx = overlay_name.indexOf("@"); 
        
    	if (idx == -1) {
    		idx = 30; // maxlen
    	}
		var shortname = overlay_name.substr(0, idx); //@ is invalid in DIV tag id.

    	var count = 0;
        while(findOverlayLayer(shortname + count.toString(), overlayMaps) != -1) {
        	count++;
            //console.log("createImageOverlay incrementing index: " + overlay_name );
            // return
        }
        shortname = shortname + count.toString();
       
        /**
         * The Google Maps API calls getTileUrl when it tries to display a map's
         * tile.  This is a good place to swap in the mapid and token we got from
         * the Python script. The other values describe other properties of the
         * custom map type.
         */
         var eeMapOptions = {
           getTileUrl: function(tile, zoom) {
             var url = ['https://earthengine.googleapis.com/map',
                        map_id, zoom, tile.x, tile.y].join("/");
             url += '?token=' + token;
             pendingUrls.push(url);
             maxPendingUrls++;
             
             if (pendingUrls.length === 1) {   
                  $(overlay).trigger("overlay-busy");   
             }
             return url;
           },
           tileSize: new google.maps.Size(256, 256)
         };

        // Create the map type.
      
        var overlay = new google.maps.ImageMapType(eeMapOptions);
        overlay.name = shortname;
        overlay.color = color;
        overlay.map = google_map;
        overlay.overlaytype = 'image';
        // Listen for our custom events
        $(overlay).bind("overlay-idle", function() {
            console.log("Finished loading overlay tiles"); 
            
            var progress = $('#tile-progress-c');
            progress.fadeOut(1200);
            maxPendingUrls = 0;
            progress.attr('max', 0);
            progress.attr('value', 0);
            //progress.width(0);
        });

        $(overlay).bind("overlay-busy", function() {
            console.log("Loading overlay tiles"); 
            var progress = $('#tile-progress-c');
            progress.stop(); //stop any fadeOut 
            progress.show();
            
        });


        // Copy the original getTile function so we can override it, 
        // but still make use of the original function
        overlay.baseGetTile = overlay.getTile;

        // Override getTile so we may add event listeners to know when the images load
        overlay.getTile = function(tileCoord, zoom, ownerDocument) {

            // Get the DOM node generated by the out-of-the-box ImageMapType
            var node = overlay.baseGetTile(tileCoord, zoom, ownerDocument);

            // Listen for any images within the node to finish loading
            $("img", node).on("load", function() {
            	console.log('tile loaded');
                // Remove the image from our list of pending urls
                var index = $.inArray(this.__src__, pendingUrls);
                pendingUrls.splice(index, 1);

                // If the pending url list is empty, emit an event to 
                // indicate that the tiles are finished loading
                //console.log("waiting for urls:"  + pendingUrls.length);
                if (pendingUrls.length === 0) {
                    $(overlay).trigger("overlay-idle");
                }
                else 	{
	                var progress = $('#tile-progress');
	                progress.attr('max', maxPendingUrls);
	                progress.width(maxPendingUrls);
	                var waiting = maxPendingUrls-pendingUrls.length;
	                progress.attr('value', waiting);
	                $('#tile-progress-label').html("Loaded " + waiting.toString() + " of " + maxPendingUrls.toString() + " tiles");
                }
            });

            return node;
        };
        var z;
        if(operation == 'show')
        {
	        google_map.overlayMapTypes.push(null); //  Placeholder for layer
	        z  = google_map.overlayMapTypes.length-1;
	        overlay.index = z;
	        google_map.overlayMapTypes.insertAt(z, overlay);
        }
        else //wipe
        {
	        google_map.overlayMapTypes.push(null); //  Placeholder for layer
	        z  = google_map.overlayMapTypes.length-1;
	        overlay.index = z;
	        google_map.overlayMapTypes.insertAt(z, overlay);
        }
        addLayer(shortname, overlay_name, color,  100, tooltip , layerslider_callback ); //create slider.
             
        overlayMaps.push(overlay);
        
        google.maps.event.addListenerOnce(google_map, 'idle', function(){
            console.log("map is idle");
        });
        return overlay;      
    }
    else 
    {
        return removeFromMap(google_map, slider_name.substring(5) );
    }  
}

function findOverlayLayer(layer_id, overlayMaps){
	"use strict";
    for (var i=0; i < overlayMaps.length; i++) {
        if (overlayMaps[i].name === layer_id)
            return i;
    }
    return -1;
}

function removeFromMap(map, overlay_id)
{
	"use strict";
    //TODO: hide slider
    //overlay = overlayMaps.pop(); //needs to be a splice not a pop.
    //overlay.hide();
}

function removeJob(job_id)
{
	"use strict";
	var panel = $("#jobs_table");
    //console.log("panel", panel);
    console.log("removeJob id:", job_id);
    var jobid = "#" + job_id;
    var job = panel.find(jobid);
    job.fadeOut(800);
}

function updateJob(job_id, text, colour)
{
	"use strict";
    var panel = $("#jobs_table");
    var jobid = "#" + job_id;
    console.log("updateJob, id:", jobid);
    var job = panel.find(jobid);
    
    var label = job.find("#tlabel_id");
    console.log("label", label);
    console.log("label.html", label.html());
    
    label.html(text).css({
		color: colour
	});
}

function addJob(text, colour)
{
	"use strict";
    var newDiv = $("#JobTemplate").clone();
    if (newDiv === 'undefined') {
    	console.log("missing JobTemplate template div in HTML");
    	return 0;
    }
    // This id should be different for each instance.
    var job_id = "job_id" + (numjobs++).toString();
        
    newDiv.attr("id", job_id);
    newDiv.id=job_id;
    
    var cross = newDiv.find("#tcross_id");
 
    cross.on('click', '' , function(){
       $(this).parent().fadeOut(700);  
    });
    
    var label = newDiv.find("#tlabel_id");
    
    label.html(text).css({
		color: colour
	});
    
    newDiv.show();
    $("#jobs_table").append(newDiv);
    console.log("addJob id:" +  job_id + " " + text);
    return job_id;
}