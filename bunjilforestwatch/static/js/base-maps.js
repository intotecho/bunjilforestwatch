/**
 * @name base=maps.js 
 * @version 1.0
 * @author Chris Goodman 
 * @copyright (c) 2012-2015 Chris Goodman 
 * @fileoverview Shows a map with before an after views of an observation
 *Your mission is to observe the latest images on the left map,<br>"  
 *         "and check for forest changes by comparing with the older image on the right map.<br>"
 *         "You may change the visualisation settings to NDVI and click <b>View</b>.<br>"
 *         "More <a href='http://www.google.com'>help is available</a>.<br>"
 *         "Click for more info.
 */
var user_url;
var area_json;
var area_json_str;
var lhs_offset_top =0;
var lhs_offset_left =0;
var drawingManager = null;
var initial_dragger = "10%";
/* var cellarray = null; not a global*/


function drawLandsatCells(cellarray, map, layer_id) {
	"use strict";
	/* global createLandsatGridOverlay */
	/* global map_over_lhs */
	/* global layerslider_callback */
    /* global addLayer */

    createLandsatGridOverlay(map, 0.0, true, cellarray, layer_id);
    addLayer(map.landsatGridOverlay.name,
            'Landsat Cells',
            'gray',  
            0,
            "Each Landsat image covers one of these cells that overlap the area", 
            layerslider_callback );
}

function update_map_panel(map, panel) {
	"use strict";
	/* global map_over_lhs */
	/* global map_under_lhs */
    var htmlString = "<span class=divider small><strong>zoom:</strong>   " + map.getZoom() + " <br/>";
    htmlString += "Center(" + map_under_lhs.getCenter().lat().toFixed(3) + "\u00B0,  " + map_under_lhs.getCenter().lng().toFixed(3) + "\u00B0)</span>";
    $(panel).empty().html(htmlString); 
}


/**
 * Updates the panel div with lat lng values of the cursor - Called after mouse moves over the map to [position pnt.
 * Shows in the View Area/Manage Tab, MapView Accordion
 */

function update_map_cursor(map, pnt, panel) {   
	"use strict";
    var lat = pnt.lat().toFixed(4);
    var lng = pnt.lng().toFixed(4);
    var htmlString  = "Cursor( " + lat + "\u00B0, " + lng + "\u00B0)";
    //Set htmlString into the panel.
    $(panel).empty().html(htmlString);
    //console.log(htmlString);
}

/**
 * Called after Make Report when an area has been marked and user clicks next.
 * @param drawingManager
 * @param event
 */
function complete_report(drawingManager, event) {
	'use strict';
	var user_name = $('#user_name').text();
	var href = '/' + user_name +
				 '/journal/Observations for ' + 
				area_json.properties.area_name; 
				 
				
	if (view_mode ===  "view-obstask") {
		href 	+= '/new?sat_image=' +
				observations[0].image_id;
	}
	window.location.href = href; //+ mapobj.id;
	console.log(event);
}




/**
 * return a center location as a latlng
 */

function areaLocation(area_json) {
	"use strict";
    "global get_area_feauture";
	var area_location_feature = get_area_feature(area_json, "area_location");
	if (area_location_feature !== null) {
		var area_location = area_location_feature.geometry.coordinates;  // init global.
		var latlng = new google.maps.LatLng(area_location[1], area_location[0]);
		return latlng;
	}
	return null;
}


function initialize() {
	"use strict";
	
	user_url    = $('#user_url').text();
	var user_name = $('#user_name').text();
	area_json_str = $('#area_json').text();
	if (area_json_str !== "") {
		try {
			area_json = jQuery.parseJSON( area_json_str);
		} catch(e){
			addToasterMessage('alert-danger', 'initialized() error ' + e + ' in area_json ' + area_json_str ); 
			return;
		}
	}

	/* global center_mapview */
	/* global zoom_mapview */
  	var map_center = center_mapview(area_json);
    var map_zoom =   zoom_mapview(area_json);
	
    /* global map_options */ 
    map_options.mapTypeId = google.maps.MapTypeId.HYBRID;
    map_options.center = map_center;
    map_options.zoom = map_zoom;
    map_under_lhs    = new google.maps.Map(document.getElementById("map-left-prior"), map_options);
	/* global map_rhs */
    map_rhs          = new google.maps.Map(document.getElementById("map-right"), map_options);

    map_options.mapTypeId = google.maps.MapTypeId.TERRAIN;
    map_over_lhs     = new google.maps.Map(document.getElementById("map-left-latest"), map_options);
    
    /* global map_under_lhs */ 
    /* global map_under_lhs */ 
    /* global map_rhs */ 
    /* global single_map*/ 
    
    if (single_map === true){
        initial_dragger = "5%";
        $('#map-right-c').hide();
        $('#map-left-c').removeClass('col-md-5');
        $('#map-left-c').addClass('col-md-10');
    }
    else {
        initial_dragger = "90%";
    }

    $('#dragger').dblclick( function(){
        console.log('double clicked handle');
    });


    $('#dragger').css('left', initial_dragger );
    map_rhs.bindTo('center', map_under_lhs);
    map_rhs.bindTo('zoom', map_under_lhs);
    
    map_over_lhs.bindTo('center', map_under_lhs);
    map_over_lhs.bindTo('zoom', map_under_lhs);
    
    var share = area_json.properties.shared; //$('#area_share').text(); 
    
    if (share === 'public')
    {
        $("#public").prop("checked", true);         
    }
    else if (share === 'unlisted')
    {
        $("#unlisted").prop("checked", true);          
    }
    else    if (share === 'private')
    {
        $("#private").prop("checked", true);          
    }
    else
    {
        console.log('area.share unrecognised state %s', share);
    }


    // Update Area Shared property
    $('#shared_form input').on('change', function() {
        var selection = $('input[name=opt-sharing]:checked', '#shared_form').val();
        //console.log("share returned: ", selection);
        
        /* global updateAreaShared */
        //updateAreaShared(selection); //ajax call
    
        var patch_ops = [
            { "op": "replace", "path": "/properties/shared", "value": selection, "id": "shared_form"}
    	];
        /* global patch_area */
        var request = patch_area(patch_ops, area_json.properties.area_url);  //patch_area(); //ajax call
        request.done(function (data) {
        	if(typeof data !== 'undefined') {
        		console.log ('patch_area() - result: ' + data.status + ', ' + data.updates.length + ' updates: ' + data.updates[0].result);
        	}
        });
        
        request.fail(function (xhr, textStatus, error) {
        	$('#area_sharing_heading').html("Sharing: failed");
			console.log ('patch_area() - request failed:', xhr.status, ' error: ', error);
        });
     });

    init_area_descriptions(area_json.properties.area_url);
    
    google.maps.event.addListener(map_under_lhs, 'bounds_changed', function() {        
        update_map_panel(map_under_lhs, '#map_panel_data');    
    });

    google.maps.event.addListener(map_under_lhs, 'mousemove', function (event) {
        update_map_cursor(map_under_lhs, event.latLng, '#map_panel_cursor');               
    });
      
    google.maps.event.addListener(map_over_lhs, 'mousemove', function (event) {
        update_map_cursor(map_over_lhs, event.latLng, '#map_panel_cursor');               
    });
   
    google.maps.event.addListener(map_rhs, 'bounds_changed', function() {    

    });
    
    google.maps.event.addListener(map_under_lhs, 'zoom', function() { 
    });

    google.maps.event.addListener(map_rhs, 'zoom', function() { 
    });

    google.maps.event.addListener(map_under_lhs, 'idle', function() {
            //This is needed so the fusion tables query works
            var map_center = map_under_lhs.getCenter();
            if (map_center.lng() < -180) { 
                map_under_lhs.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng()+360));
            }
            if (map_center.lng() > 180) { 
                map_under_lhs.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng()-360));
            }
            
            //map_rhs.setCenter(map_center);
    });

    /* displayBoundaryHull */
    /* global overlayMaps */
    /* global addLayer */

    var areaBoundary = displayBoundaryHull(map_under_lhs, area_json); // draw area's boundary or area_location marker
    overlayMaps.push(areaBoundary);
    addLayer(areaBoundary.name,
        area_json.properties.area_name + " Border",
        "yellow",
        50,
        "Boundary of Area " + area_json.properties.area_name,
        layerslider_callback);

    // draw area's boundary or area_location marker

    var newData = createDataLayer(map_over_lhs, false); // not editable

	newData = displayFeatureCollection(map_over_lhs, area_json.boundary_geojson);
    if (newData !== null) {
        newData.name = "geometry";
        newData.overlaytype = 'data';
        newData.setMap(map_over_lhs);
		overlayMaps.push(newData); //map_over_lhs.data
	    addLayer("geometry",
	    		area_json.properties.area_name + " Geometry",
	    		"green",
	    		50,
	    		"Geometry of Area " + area_json.properties.area_name,
	    		layerslider_callback);
    }

    if (typeof(area_json.glad_alerts) !== 'undefined' ) {
        console.log(area_json.glad_alerts);
        var layer = new google.maps.FusionTablesLayer({
            query: {
                select: 'latlong',
                from: area_json.glad_alerts
            },
             styles: [
             {
                markerOptions: {
                    iconName: "small_pink"
                }
             }
            ]
        });

        layer.overlaytype = 'fusion';
        layer.name = 'gladalerts';
		overlayMaps.push(layer); //map_over_lhs.data
  		layer.setMap(map_under_lhs);
		addLayer("gladalerts",
			"Glad Alerts",
			"pink",
			100,
			"Alerts" + area_json.properties.glad_alerts,
			layerslider_callback);
    }
 	if (typeof(area_json.glad_clusters) !== 'undefined' ) {
 	
		newData = displayFeatureCollection(map_under_lhs, jQuery.parseJSON(area_json.glad_clusters));
		if (newData !== null) {
			newData.name = "clusters";
			newData.overlaytype = 'data';
			newData.setMap(map_under_lhs);
			overlayMaps.push(newData); //map_over_lhs.data
			addLayer("clusters",
					"Alert Clusters",
					"pink",
					100,
					"Clusters" + area_json.properties.area_name,
					layerslider_callback);
		}
 	}

        /*  if AOI is new, then need to ask earthengine to calculate what cells overlap the areaAOI.
     *  This is done here the first time the area is viewed. But could be part of constructor for AreaOfInterest.
     */
    var cellarray = jQuery.parseJSON($('#celllist').text());
 
   
   if(cellarray.length === 0) {
        // calculate and fetch the overlapping cells from server.
        fetch_landsat_cells(area_json);
   }
   else
   {
       // server passed an existing cellarray -  don't wait for ajax - just display it.
       drawLandsatCells(cellarray, map_over_lhs, "grid_over");
       //drawLandsatCells(cellarray, map_under_lhs, "grid_under");
   }

    
    var observations = jQuery.parseJSON($('#obslist').text());
    /* global displayObsOverlay */
    for (var i=0; i < observations.length; i++) {        
        displayObsOverlay(observations[i], 'latest', 'rgb'); //LHS overlay(s)
        displayObsOverlay(observations[i], 'prior', 'rgb'); //RHS overlays(s)        
     }
 
    // View button will fetch Latest Overlay Image of selected (last clicked) cell on LHS.
    /* global requestAdHocOverlay */
    $('#get_overlay_btn').click(function(){
        requestAdHocOverlay();
        
    }); //get_overlay_btn.click

     /* global createDrawingManager */
    $('#make-report').click(function(){
    	console.log("make report");
        $('#make-report-popover').popoverX('show');
        if (drawingManager  === null){
        	map_over_lhs.drawingTools = new DrawingTools(map_over_lhs, mapContainer, dropContainer, geoJsonPanel, geoJsonInput, downloadLink);
        	drawingManager  = createDrawingManager(map_over_lhs, google.maps.drawing.OverlayType.POLYGON); //FIXME Don't draw more than one.
        	google.maps.event.addListener(drawingManager, 'overlaycomplete', function(event) {
        		complete_report(drawingManager, event);
            });
        }
     });
    
     $('#make-report-popover-close').click(function(){
        $('#make-report-popover').popoverX('hide');
     });

     $('#make-report-popover-next').click(function(){
    	 //load page
         $('#make-report-popover').popoverX('hide');
      });

     $('#edit-boundary').click(function(){
     	console.log("edit boundary");
        $('#edit-boundary-popover').popoverX('show');
      });
     
      $('#edit-boundary-popover-close').click(function(){
         $('#edit-boundary-popover').popoverX('hide');
      });

      $('#edit-boundary-popover-next').click(function(){
    	 
          $('#edit-boundary-popover').popoverX('hide');
    		var href = '/area/' + area_json.properties.area_name +
    					 '/boundary'; 
    		window.location.href = href; //+ mapobj.id;
    		console.log(event);
       });
      
    $('#sign-in').click(function(){
        $('#sign-in-popover').popoverX('show');
     });
   
    $('#close-popover-sign-in').click(function(){
        $('#sign-in-popover').popoverX('hide');
    });
    
    $('#do-popover-sign-in').click(function(){
    	console.log("do sign-in");
        $('#sign-in-popover').popoverX('hide');
    	window.location.href = "/login/google";
    });
    
    //Change the text in the drop-down button when a selection is changed.
    $('#algorithm-visual').click(function(e){
           $("#algorithm:first-child").text("RGB");
           //algorithm = 'rgb';
           e.preventDefault();
        });
        $('#algorithm-ndvi').click(function(e){
           $("#algorithm:first-child").text("NDVI");
           //algorithm = 'ndvi';
           e.preventDefault();
        });
        $('#algorithm-change').click(function(e){
           $("#algorithm:first-child").text("Change");
           //algorithm = 'change';
           e.preventDefault();
        });
        
        $('#latest').click(function(e){
            $("#latest:first-child").text("Latest  ");
            //latest = 0;
            e.preventDefault();
        });
        $('#latest-1').click(function(e){
            $("#latest:first-child").text("Latest-1");
            //latest = 1;
            e.preventDefault();
        });
        $('#latest-2').click(function(e){
            $("#latest:first-child").text("Latest-2");
            //latest = 2;
            e.preventDefault();
        });
        $('#latest-3').click(function(e){
            $("#latest:first-child").text("Latest-3");
            //latest = 3;
            e.preventDefault();
        });
        
        $('#satellite').click(function(e){
            $("#satellite:first-child").text("L8");
            //satellite = 'l8';
            e.preventDefault();
        });
        $('#satellite-l7').click(function(e){
            $("#satellite:first-child").text("L7");
            //satellite = 'l7';
            e.preventDefault();
        });
        $('#satellite-both').click(function(e){
            $("#satellite:first-child").text("Both");
            //satellite = 'l78';
            e.preventDefault();
        });
        
        $('#save-view').click(function(){
        	save_view(map_under_lhs, area_json);
        });

        
        $(window).resize(function () {
                //<!--resize tip from //github.com/twitter/bootstrap/issues/2475 -->
                var h = $(window).height(),
                offsetTop = 30; // Calculate the top offset
                $('#map-left-c').css('height', (h - offsetTop));
                $('#map-left-latest').css('height', (h - offsetTop));
                $('#map-left-prior').css('height', (h - offsetTop));
                $('#map-right').css('height', (h - offsetTop));
                $('#map-left-latest').width('100%');
                $('#map-left-prior').width( $('#map-left-latest').width() );
                //$('#map-left-prior').width($(window).width());
                $('#dragger').css('height', (h - offsetTop));
                
                //get offset of rhs map cursor (and offset for half size of cursor)
                lhs_offset_top = $('#map-left-c-prior').offset().top+10;
                lhs_offset_left  = $('#map-left-c-prior').offset().left+1;
                
                //google.maps.event.trigger(mapStyled, 'resize');
            }).resize();

        //var save_view_instructions = 
           
        $('#save-view').popover({ 
            html : true, 
            animation: true,
            trigger: 'hover',
            container: 'body',
            title: 'Save View',  
            placement: 'bottom',
            content:  "Save the current view.<br/>" +
            "All users will see this as the initial view when they open an observation for this area. <br/>"
            });

        //var reset_view_instructions = 
            
        $('#reset-view').popover({ 
            html : true, 
            animation: true,
            trigger: 'hover',
            container: 'body',
            title: 'Reset View',  
            placement: 'bottom',
            content: "Return map to the initial view.<br/>" +
            "This does not update the saved view.<br/>"
            });
        
        $('#reset-view').click(function(){
        	console.log('reset-view:');
        	var map = map_under_lhs;
    
            var map_zoom =   zoom_mapview(area_json);
	        map.setZoom(map_zoom);

        	var map_center = center_mapview(area_json);
            map.setCenter(map_center);
        });
        
        
        $('#lock-map-rhs').click(function(e){
            alert ("lock map - not implemented");
            console.log("lock map");
        });

        $('#expand-map-rhs').click(function(e){
           if(e.target.checked) {
                $('#map-right-c').hide();
                $('#map-left-c').removeClass('col-md-5');
                $('#map-left-c').addClass('col-md-10');
           }
           else {
                  $('#map-left-c').removeClass('col-md-10');
                  $('#map-left-c').addClass('col-md-5');        
                  $('#map-right-c').show();
           }
           google.maps.event.trigger(map_under_lhs,'resize');
           // google.maps.event.trigger(map_rhs,'resize');
        });
        
        $('#map-left-c-prior').width(initial_dragger); // must be same value as {dragger:left} to init correctl
        //$('#draghandle-c').width('12px').height('12px');
        //$('#draghandle').width('11px').height('11px');
  
        $('#dragger').udraggable({
            axis: 'x',
            containment: 'parent',
            helper: "$('#draghandle')",
            /*handle: '#draghandle',*/
            /*cursor: 'col-resize',*/
            drag: function(e, u) {
              var left = u.position.left;
              $('#map-left-c-prior').width(left);
                if(left < 20) {
                    console.log(left);
                    $('#draghandle').attr("{background-color:blue}");
                }
              //$('#draghandle').width('11px').height('11px');
            }
        });
        
        $("#map-left-c-prior").on({
            mousemove: function(e){
                var x = e.pageX - lhs_offset_left;
                var y = e.pageY - lhs_offset_top;
                $("#rhs_cursor").css({left: x, top: y});
            }
        });
        
        $("#map-left-c-latest").on({
            mousemove: function(e){
                var x = e.pageX - lhs_offset_left;
                var y = e.pageY - lhs_offset_top;
                $("#rhs_cursor").css({left: x, top: y});
             }
        });

        $("#map-left-c").on({
            mouseleave: function(){
                $("#rhs_cursor").hide(); 
                //console.log('hide');
            },
            
            mouseenter: function(){
                $("#rhs_cursor").show(); 
                //console.log('show');
            }
        });

        /* global toggle_edit_cells_lock */ 
        $('#edit-cells-lock').click(function(e){
            toggle_edit_cells_lock();
        });
        toggle_edit_cells_lock();  // call during init to draw div
    
} //end-of-initialize

/**
 *  Fetching outline of landsat cells overlapping Area
 *  These need to be calculated by the server. See send a request that adds a job.
 */
function fetch_landsat_cells(area_json) {
        console.log("Init: Fetching Overlapping Cells for Area");
        var url = area_json.properties.area_url + '/getcells';
        
        $('#cell_panel_title').collapse('show');       //open  cell_panel_title to set height.
        
        $('#dialog-new-cells').popoverX({
            target: '#cell_panel_t'  //container
        });
        $('#dialog-new-cells').popoverX('show');
        setTimeout(function() {
            $('#dialog-new-cells').popoverX('hide');
        }, 80000);
		
        var prompt = "<h6><small>Calculating Cells</small></h6><img src='/static/img/ajax-loader.gif' class='ajax-loader'/>";
        /* global addJob */
        var jobid = addJob(prompt, 'gray');

		$('#close-dialog-new-cells').click(function(){
			$('#dialog-new-cells').popoverX('hide');
		});

		$('#close-dialog-new-cells-open-accordion').click(function(){
			$('#cell_panel_title').collapse('show');       //open  cell_panel_title
			$('#dialog-new-cells').popoverX('hide');
	    }); 

        var request = jQuery.ajax({
    	    type: "GET",
    	    url: url //area_json.properties.area_url,
    	});

        request.done(function (data) {
	          var getCellsResult = jQuery.parseJSON(data);
	            
	            if (getCellsResult.result === 'success'){
	                cellarray = getCellsResult.cell_list;
	                console.log('GetCells result: ' + getCellsResult.result + ' reason: ' + getCellsResult.reason);
	         
	                var plurals = (cellarray.length === 1)? ' cell covers': ' cells cover';
	                var plurals_mon = (getCellsResult.monitored_count === 1)? ' cell selected': ' cells selected';
	                /* global updateJob */
	                updateJob(jobid, "<p class = 'small'>" + cellarray.length  + plurals + "  your area. " + getCellsResult.monitored_count + plurals_mon + '</p>', 'black');
	                drawLandsatCells(cellarray, map_over_lhs, "grid_over");
			        drawLandsatCells(cellarray, map_under_lhs, "grid_under");
	            }            
	            else
	            {
	                updateJob(jobid,"<p class = 'small'>GetCells Failed:" + getCellsResult.reason + "</p>", 'red');
	                //TODO: Redirect to home?
	            }
	    });	
	        
	    request.fail(function (xhr, textStatus, error) {
            var msg = xhr.status + ', ' + error; 
            console.log( "GetCells Failed: " + msg);
            updateJob(jobid, "<p class = 'small'>GetCells Failed: " + msg + "</p>",'red');
	    });
}






google.maps.event.addDomListener(window, 'load', initialize); 


function httpgetActionUrl(action)
{
	"use strict";
	var satellite = $("#satellite:first-child").text().trim();
	var algorithm = $("#algorithm:first-child").text().trim();
	var latest_str= $("#latest:first-child").text().trim();
	var latest;
	switch (latest_str) {
		case "Latest-1":
		    latest = 1;
		    break;
		case "Latest-2":
		    latest = 2;
		    break;
		case "Latest-3":
		    latest = 3;
		    break;
		default: 
			latest = 0;
	}    
	    
	var path = map_over_lhs.landsatGridOverlay.selectedPath;
	var row  = map_over_lhs.landsatGridOverlay.selectedRow;
	
	var url =  area_json.properties.area_url  + '/action/' + action + '/' + satellite + '/' + algorithm + '/' + latest;
	  
	    if((path !== -1) && (row !== -1))
	    {
	        url  += "/" + path + "/" + row;
	}
	return url;
}


