/*******************************************************************************
 * Copyright (c) 2014 Chris Goodman GPLv2 Creative Commons License to share
 * See also https://developers.google.com/maps/documentation/javascript/examples/overlay-hideshow
 ******************************************************************************/
var overlayMaps = [];
var jobs = [];
var numjobs = 0;

function createLandsatGridOverlay(map, opacity, clickable, cellarray) { 
    if (map.landsatGridOverlay === undefined){
        var landsatGridOverlay = new LandsatGridOverlay(map, opacity, clickable, cellarray);
        landsatGridOverlay.name = "grid" ;
        landsatGridOverlay.initialize();
        
        overlayMaps.push(landsatGridOverlay);
        /*
        addLayer( landsatGridOverlay.name,
                  'Landsat Cell Border',
                  'gray',  
                  100 * opacity, 
                  "Each Landsat image covers one of these cells.", 
                  layerslider_callback ); //create slider.
        */
        map['landsatGridOverlay'] = landsatGridOverlay;
    }
}
   


//find overlay mathching role and viz algorithm.
function findOverlay(obs, role, algorithm) {
    for (o = 0; o < obs.overlays.length; o++) {
        var overlay = obs.overlays[o];
        if ((overlay.overlay_role == role) && (overlay.algorithm == algorithm)) {
        	return overlay;
        }         
    }
    return null;
}


function requestAdHocOverlay() { //not assoc with a task...
 	var httpget_url = httpgetActionUrl("overlay")
    console.log( "urls", httpget_url);
	
	fetchOverlay(null, "prompt for new overlay", httpget_url );
	
}


function displayOverlay(ovl, overlayname, tooltip) { //overlay is current so add it to the map.
    
    var map =    ((ovl.overlay_role == 'latest') ?  map_lhs : map_rhs);    
    var colour; 
    
    if (ovl.overlay_role == 'latest') 
    	colour = 'red';
    else if (ovl.overlay_role == 'prior') 
    	colour = 'green'  
    else 
    	colour = 'blue';
    
    //addJob("<p class = 'small'>" + ovl.reason +"</p><br>")

    createImageOverlay(true, map, ovl.map_id,  ovl.token, overlayname, tooltip, colour);
}

function fetchOverlay(obs, prompt, httpget_url) {	
      prompt += '<img src="/static/img/ajax-loader.gif" class="ajax-loader"/>';
      jobid = addJob(prompt, 'black');
      
      $.get(httpget_url).done(function(data) {
	       var tooltip;
	       var overlayname;
	       var ovl = jQuery.parseJSON(data);
	   
	       if (ovl) {
	    	   if (obs != null ) {
		    	   	tooltip = "Overlay: " +  obs.captured  +  " Id: " + obs.image_id + " " + ovl.overlay_role + " " + ovl.algorithm;
		            overlayname = obs.captured + ":" + ovl.overlay_role;          
		       }
		       else {
		    	   	tooltip = "AdHoc overlay";
		            overlayname = tooltip;        
		       }
		       if (ovl.result =='error')
		    	   {
	    	   		updateJob(jobid, "<p class = 'small'>" + ovl.reason +"</p><br>", 'red');
		    	   }
		       else {
		    	   removeJob(jobid);
		    	   displayOverlay(ovl, overlayname, tooltip);
		       }
	       }
	       else {
	    	   		updateJob(jobid, "<p class = 'small'>No Overlay Data</p><br>", 'red');

	       }
	  }).error(function( jqxhr, textStatus, error ) {
	           var err = textStatus + ', ' + error;
	           console.log( "Request Failed: " + err);
	           updateJob(jobid, "<p class='small'>Failed: " + err + "</p><br>", 'red');
	  });
}

function updateOverlay(ovl, overlayname, tooltip) {
    
	var prompt  = "Updating " + ovl.overlay_role + " "  + ovl.algorithm;

	var httpget_url = 'overlay/update/' + ovl.key + '/' + ovl.algorithm; 
    
    console.log( "updateOverlay() %s as: %s", prompt, httpget_url);
    fetchOverlay(obs,'<small>' + prompt + '</small>', httpget_url );
}

function createObsOverlay(obs, role, algorithm) {
	
	var httpget_url = 'overlay/create/' + obs.key + '/' + role + '/' + algorithm; 
	
	var prompt  = "Creating " + role + " "  + algorithm + " overlay";
       
    console.log( "createObsOverlay() %s as: %s", prompt, httpget_url);
    
    fetchOverlay(obs, '<small>' + prompt + '</small>', httpget_url);
}


function displayObsOverlay(obs, role, algorithm) {

    var ovl = findOverlay(obs, role, algorithm);
    
    if (ovl != null) {
    	
    	var test_tile_url = ['https://earthengine.googleapis.com/map', ovl.map_id, 1, 0, 0].join("/");
    	test_tile_url += '?token=' + ovl.token

    	var tooltip = "Overlay: " +  obs.captured  +  " Id: " + obs.image_id + " " + ovl.overlay_role + " " + ovl.algorithm;
        var overlayname = obs.captured + ":" + ovl.overlay_role;          

    	$.get(test_tile_url).done(function(data) {
    	       console.log("Overlay tiles are OK ")
               displayOverlay(ovl, overlayname, tooltip);
    	      
        }).error(function( jqxhr, textStatus, error ) {
                console.log("Overlay needs refreshing");
                updateOverlay(ovl, overlayname, tooltip);
        });
    }
    else {
        createObsOverlay(obs, role, algorithm);
    }
}    
 
 
/*      
 * createImageOverlay(true, map_lhs, mapobj.mapid,  mapobj.token, mapobj.date_acquired, tooltip, "cyan");
 * 
 */
function createImageOverlay(show, google_map, map_id,  token, overlay_name, tooltip, color)
{
    if(show == true)
    {
        var shortname = overlay_name.substr(0, overlay_name.indexOf("@")); //@ is invalid in DIV tag id.
            
        var count = 0;
        while(findOverlayLayer(shortname + count.toString(), overlayMaps) != -1) {
        	count++;
            console.log("createImageOverlay incrementing index: " + overlay_name );
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
             url += '?token=' + token
             return url;
           },
           tileSize: new google.maps.Size(256, 256)
         };

        // Create the map type.
      
        var overlay = new google.maps.ImageMapType(eeMapOptions);
        overlay.name = shortname;
        overlay.color = color;
        overlay.map = google_map;

        
        google_map.overlayMapTypes.push(null); //  Placeholder for layer
        z  = google_map.overlayMapTypes.length-1;
        overlay.index = z;
        google_map.overlayMapTypes.insertAt(z, overlay);
        
        addLayer(shortname, overlay_name, color,  100, tooltip , layerslider_callback ); //create slider.
      
        overlayMaps.push(overlay);
    }
    else 
    {
        removeFromMap(google_map, slider_name.substring(5) );
    }
    return overlay
}


function findOverlayLayer(layer_id, overlayMaps){
	//    return $.grep(overlayMaps, function(obj){
	//        return obj.name == layer_id;
	//  });

    for (var i=0; i < overlayMaps.length; i++) {
        if (overlayMaps[i].name == layer_id)
            return i;
    }
    return -1;
}


function layerslider_callback(layer_id, val) {
    console.log("layerslider_callback : " + layer_id + ", " + val);
    
    var id = findOverlayLayer(layer_id, overlayMaps);
    if (id != -1) {
        console.log("layerslider_callback:" + overlayMaps[id].name + ", " + val); //overlayMaps[id].name
        //console.log(typeof overlayMaps[id]); 
        if(overlayMaps[id].name == 'boundary') { //TODO: Too brittle. Need better way to determine objct type.
        	 overlayMaps[id].setOptions({strokeOpacity :val/100} );
        	 
        }
        else {
        	overlayMaps[id].setOpacity(Number(val)/100);
        }
    }
}


function removeFromMap(map, overlay_id)
{
    //TODO: hide slider
    //overlay = overlayMaps.pop(); //needs to be a splice not a pop.
    //overlay.hide();
}


function removeJob(job_id)
{
  var panel = $("#jobs_table");
    console.log("panel", panel);
    jobid = "#" + job_id;
    var job = panel.find(jobid);
    job.fadeOut(800);
}

function updateJob(job_id, text, colour)
{
    var panel = $("#jobs_table");
    jobid = "#" + job_id;
    var job = panel.find(jobid);
    console.log("job", job);
    
    var label = job.find("#tlabel_id");
    console.log("label", label);
    console.log("label.html", label.html());
    
    label.html(text).css({
		color: colour
	});
}

function addJob(text, colour)
{
    var newDiv = $("#JobTemplate").clone();
    if (newDiv === 'undefined') {
    	console.log("missing JobTemplate template div in HTML");
    	return 0;
    }
    // This id should be different for each instance.
    job_id = "job_id" + (numjobs++).toString();
        
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
    return job_id;
}