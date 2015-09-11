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
var border_latlngs = [];
var drawingManager = null;
var initial_dragger = "90%";
/* var cellarray = null; not a global*/


function drawLandsatCells(cellarray) {
	"use strict";
	/* global createLandsatGridOverlay */
	/* global map_over_lhs */
	/* global layerslider_callback */
    /* global addLayer */

    createLandsatGridOverlay(map_over_lhs, 0.5, true, cellarray);
    addLayer( map_over_lhs.landsatGridOverlay.name,
            'Landsat Cells',
            'gray',  
            75, 
            "Each Landsat image covers one of these cells.", 
            layerslider_callback );
}

function update_map_panel(map, panel) {
	"use strict";
	/* global map_over_lhs */
	/* global map_under_lhs */
    var htmlString = "<span class=divider small><strong>zoom:</strong>   " + map.getZoom() + " <br/>";
    //htmlString += "<strong>center:</strong><br>";
    htmlString += "Center(" + map_under_lhs.getCenter().lat().toFixed(3) + ",  " + map_under_lhs.getCenter().lng().toFixed(3) + ")</span>";
    $(panel).empty().html(htmlString); 
}


//update_map_cursorupdates the panel div with values of the cursor in long based after map becomes idle.

function update_map_cursor(map, pnt, panel) {   
	"use strict";
    var lat = pnt.lat();
    lat = lat.toFixed(4);
    var lng = pnt.lng();
    lng = lng.toFixed(4);
    var htmlString  = "Cursor( " + lat + ", " + lng + ")";
    $(panel).html(htmlString); 
}


function initialize() {
	"use strict";
	
	user_url    = $('#user_url').text();
	var user_name = $('#user_name').text();
	area_json_str = $('#area_json').text();
	if (area_json_str !== "") {
		area_json = jQuery.parseJSON( area_json_str);
	}
	else	{
		alert("missing area data");
		return;
	}
	var center_coords = area_json.features[0].geometry[0].coordinates;  // init global.
    var map_center = new google.maps.LatLng(center_coords[0], center_coords[1]);
	var map_zoom = area_json.features[0].properties.map_zoom;  // init global.
     
    var mapOptions_latest = {
        zoom: map_zoom,
        center: map_center,    
        mapTypeId: google.maps.MapTypeId.HYBRID,
        panControl:true,
        zoomControl:true,
        mapTypeControl:true,
        streetViewControl:false,
        overviewMapControl:false,
        rotateControl:false,
        clickable: true,
        scaleControl: true //        scaleControlOptions: {position: google.maps.ControlPosition.BOTTOM_LEFT}
    }

    var mapOptions_prior = {
            zoom: map_zoom,
            center: map_center,    
            mapTypeId: google.maps.MapTypeId.TERRAIN,
            panControl:true,
            zoomControl:true,
            mapTypeControl:true,
            streetViewControl:false,
            overviewMapControl:false,
            rotateControl:false,
            clickable: true,
            scaleControl: true,
            scaleControlOptions: {position: google.maps.ControlPosition.BOTTOM_RIGHT}
        }
    /* global map_under_lhs */ 
    /* global map_under_lhs */ 
    /* global map_rhs */ 
    /* global single_map*/ 
    map_under_lhs      = new google.maps.Map(document.getElementById("map-left-prior"), mapOptions_prior);
    map_over_lhs    = new google.maps.Map(document.getElementById("map-left-latest"), mapOptions_latest);
    map_rhs               = new google.maps.Map(document.getElementById("map-right"), mapOptions_prior);
    
    if (single_map === true){
        initial_dragger = "10%";
        $('#map-right-c').hide();
        $('#map-left-c').removeClass('col-md-5');
        $('#map-left-c').addClass('col-md-10');
    }
    else {
        initial_dragger = "90%";
    }
    $('#dragger').css('left', initial_dragger );
    
    map_rhs.bindTo('center', map_under_lhs);
    map_rhs.bindTo('zoom', map_under_lhs);
    
    map_over_lhs.bindTo('center', map_under_lhs);
    map_over_lhs.bindTo('zoom', map_under_lhs);
    
    var share = area_json.properties.shared; //$('#area_share').text(); 
    
    if (share === 'public')
    {
        $("#public").prop("checked", true)          
    }
    else if (share === 'unlisted')
    {
        $("#unlisted").prop("checked", true)          
    }
    else    if (share === 'private')
    {
        $("#private").prop("checked", true)          
    }
    else
    {
        console.log('area.share unrecognised state %s', share);
    }

    $('#shared_form input').on('change', function() {
        var selection = $('input[name=opt-sharing]:checked', '#shared_form').val();
        console.log("share returned: ", selection);
        /* global updateAreaShared */
        updateAreaShared(selection); //ajax call
        $('#area_sharing_heading').html("Sharing: updating ...");
    });
    
    google.maps.event.addListener(map_under_lhs, 'bounds_changed', function() {        
        update_map_panel(map_under_lhs, '#map_panel_data')    
    });

    google.maps.event.addListener(map_under_lhs, 'mousemove', function (event) {
        update_map_cursor(map_under_lhs, event.latLng, '#map_panel_cursor');               
    });
    
    google.maps.event.addListener(map_over_lhs, 'mousemove', function (event) {
        update_map_cursor(map_under_lhs, event.latLng, '#map_panel_cursor');               
    });
   
    google.maps.event.addListener(map_rhs, 'bounds_changed', function() {    

    });
    
    google.maps.event.addListener(map_under_lhs, 'zoom', function() { 
    });

    google.maps.event.addListener(map_rhs, 'zoom', function() { 
    });

    google.maps.event.addListener(map_under_lhs, 'idle', function() {
            //This is needed so the fusion tables query works
            var map_center = map_under_lhs.getCenter()
            if (map_center.lng() < -180) { 
                map_under_lhs.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng()+360));
            }
            if (map_center.lng() > 180) { 
                map_under_lhs.setCenter(new google.maps.LatLng(map_center.lat(), map_center.lng()-360));
            }
            
            //map_rhs.setCenter(map_center);
    });

    //Collect the Boundary coordinates from the area and convert to a Google Maps object.
    
    
    var boundary_coords_str = '<p class="divider small">'
    var coords_arr   =  area_json.features[1].geometry.coordinates;  // init global.

    //console.log(coords_arr);
    
    for (var j=0; j < coords_arr.length; j++)
    {
        var latlng = new google.maps.LatLng(coords_arr[j].lat, coords_arr[j].lng );
        //console.logprint parseInt(coords_arr[j].lat. parseInt(coords_arr[j].lng
        border_latlngs.push(latlng);
        boundary_coords_str += latlng.toUrlValue(5) + '<br>';
    }
  
    boundary_coords_str += '</p>' //fill the accordion.html
    //console.log(boundary_coords_str);
    $('#boundary_panel').html(boundary_coords_str);
    
    //TODO: Note that Border of AOI does not adjust opacity on both overlays yet.
    var areaBoundary_over_lhs = new google.maps.Polygon({
                paths: border_latlngs,
                strokeColor: '#FFFF00',
                strokeOpacity: 0.5,
                strokeWeight: 2,
                fillColor: '#000000',
                fillOpacity: 0.05
    });
    
    var areaBoundary_under_lhs= new google.maps.Polygon({
                paths: border_latlngs,
                strokeColor: '#FFFF00',
                strokeOpacity: 0.5,
                strokeWeight: 2,
                fillColor: '#000000',
                fillOpacity: 0.05
    });
    
    var areaBoundary_rhs = new google.maps.Polygon({
        paths: border_latlngs,
        strokeColor: '#FFFF00',
        strokeOpacity: 0.5,
        strokeWeight: 2,
        fillColor: '#000000',
        fillOpacity: 0.05
    });
    
    areaBoundary_over_lhs.setMap(map_over_lhs);
    areaBoundary_under_lhs.setMap(map_under_lhs);
    areaBoundary_rhs.setMap(map_rhs);

    areaBoundary_over_lhs.name = "boundary" ;
    /* global overlayMaps */ 
    overlayMaps.push(areaBoundary_over_lhs);
    /* global addLayer */
    addLayer(areaBoundary_over_lhs.name, 
    		area_json.properties.area_name + " Border", 
    		"yellow",  
    		50, 
    		"Boundary of Area " + area_json.properties.area_name, 
    		layerslider_callback);
      
    /*  if AOI is new, then need to ask earthengine to calculate what cells overlap the areaAOI. 
     *  This is done here the first time the area is viewed. But could be part of constructor for AreaOfInterest.
     */    
    var cellarray = jQuery.parseJSON($('#celllist').text()); 
  
    var jobid = -1;

    
    $('#close-dialog-new-cells').click(function(){    
        $('#dialog-new-cells').popoverX('hide');
    }); 

    $('#close-dialog-new-cells-open-accordion').click(function(){
        $('#cell_panel_title').collapse('show');       //open  cell_panel_title
        $('#dialog-new-cells').popoverX('hide');
   }); 
    
    if(cellarray.length === 0) { // Then fetch the overlapping cells from server.
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
        jobid = addJob(prompt, 'gray');
      
        $.get(url).done(function(data) {
                        
            var getCellsResult = jQuery.parseJSON(data);
            
            if (getCellsResult.result === 'success'){
                cellarray = getCellsResult.cell_list;
                console.log('GetCells result: ' + getCellsResult.result + ' reason: ' + getCellsResult.reason);
         
                var plurals = (cellarray.length === 1)? ' cell covers': ' cells cover';
                var plurals_mon = (getCellsResult.monitored_count === 1)? ' cell selected': ' cells selected';
                /* global updateJob */
                updateJob(jobid, "<p class = 'small'>" + cellarray.length  + plurals + "  your area. " + getCellsResult.monitored_count + plurals_mon + '</p>', 'black');
                drawLandsatCells(cellarray);
            }            
            else
            {
                updateJob(jobid,"<p class = 'small'>GetCells Failed:" + getCellsResult.reason + "</p>", 'red');
                //TODO: Redirect to home?
            }
        }).error(function( jqxhr, textStatus, error ) {
            var err = textStatus + ', ' + error; 
            console.log( "GetCells Failed: " + err);
            updateJob(jobid, "<p class = 'small'>GetCells Failed: " + err + "</p>",'red');
        });
    } //get cells     
    else
    {
        //server passed an existing cellarray -  don't wait for ajax - just display it.
        drawLandsatCells(cellarray);
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

    function complete_report(drawingManager, event) {
    	
    	var href = '/' 
    				+ user_name 
    				+ '/journal/Observations for ' 
    				+ area_json.properties.area_name; 
    				 
    				
    	if (view_mode ===  "view-obstask") {
    		href 	+= '/new?sat_image=' 
    				+ observations[0].image_id;
    	}
    	window.location.href = href; //+ mapobj.id;
    	console.log(event);
    }
    /* global createDrawingManager */
    $('#make-report').click(function(){
    	console.log("make report");
        $('#make-report-popover').popoverX('show');
        if (drawingManager  === null){
        	drawingManager  = createDrawingManager(map_over_lhs); //FIXME Don't draw more than one.
        	google.maps.event.addListener(drawingManager, 'overlaycomplete', function(event) {
        		complete_report(drawingManager, event);
             });
        }
     });
    
     $('#make-report-popover-close').click(function(){
        $('#make-report-popover').popoverX('hide');
     });

     $('#make-report-popover-next').click(function(){
         $('#make-report-popover').popoverX('hide');
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
              //$('#draghandle').width('11px').height('11px');
            }
        });
        
        $("#map-left-c-prior").on({
            mousemove: function(e){
                var x = e.pageX - lhs_offset_left;
                var y = e.pageY - lhs_offset_top;
                $("#rhs_cursor").css({left: x, top: y})
            }
        });
        
        $("#map-left-c-latest").on({
            mousemove: function(e){
                var x = e.pageX - lhs_offset_left;
                var y = e.pageY - lhs_offset_top;
                $("#rhs_cursor").css({left: x, top: y});
             }
        })

        $("#map-left-c").on({
            mouseleave: function(){
                $("#rhs_cursor").hide(); 
                //console.log('hide');
            },
            
            mouseenter: function(){
                $("#rhs_cursor").show(); 
                //console.log('show');
            }
        })

        /* global toggle_edit_cells_lock */ 
        $('#edit-cells-lock').click(function(e){
            toggle_edit_cells_lock();
        });
        toggle_edit_cells_lock();  // call during init to draw div
        
        $('#delete_area_id').click(function(e) {
            	/* global bootbox */
                bootbox.dialog({
                      message: "<b>Warning!</b> Deleting this area cannot be undone.<br/>Data contained with the area will also be deleted.<br/>Volunteers who follow this area will be notified.",
                      title: "Delete Area <b>" + area_json.properties.area_name + "</b> - Are You Sure?",
                      buttons: {
                        success: {
                          label: "Cancel",
                          className: "btn-info",
                          callback: function() {
                          }
                        },
                        danger: {
                          label: "Delete",
                          className: "btn-danger",
                          callback: function() {
                              console.log("Deleting area");
                              window.location.href =  area_json.properties.area_url  + "/delete" ;
                          }
                        }
                      }
                    });
            }     
        );//delete-are-you-sure handler
} //end-of-initialize

google.maps.event.addDomListener(window, 'load', initialize); 

/**
 * action/<action> can be 'overlay' or 'download' or image.
 * @todo: satellite is 'l8' or 'l7' but should change to collection name.
 * @todo: latest is still a global var....
 */

function httpgetActionUrl(action)
{
	"use strict"
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


