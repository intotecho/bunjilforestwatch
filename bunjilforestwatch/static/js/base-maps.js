var user_url;
var area_json_str;
var lhs_offset_top =0;
var lhs_offset_left =0;
var border_latlngs = [];

google.maps.event.addDomListener(window, 'load', initialize); 

function initialize() {

	user_url    = $('#user_url').text();
	area_json_str = $('#area_json').text();
	if (area_json_str !== "") {
		area_json = jQuery.parseJSON( area_json_str);
	}
	else
	{
		//alert("missing area data");
		//return;
	}
	var center_coords = area_json['features'][0]['geometry'][0]['coordinates'];  // init global.
    map_center = new google.maps.LatLng(parseInt(center_coords.lat), parseInt(center_coords.lng) );
	map_zoom = area_json['features'][0]['properties']['map_zoom'];  // init global.
     
    var mapOptions_latest = {
        zoom: map_zoom,
        center: map_center,    
        mapTypeId: google.maps.MapTypeId.HYBRID,
        panControl:true,
        zoomControl:true,
        mapTypeControl:true,
        scaleControl:true,
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
            scaleControl:true,
            streetViewControl:false,
            overviewMapControl:false,
            rotateControl:false,
            clickable: true,
            scaleControl: true,
            scaleControlOptions: {position: google.maps.ControlPosition.BOTTOM_RIGHT}
        }
 
    map_under_lhs      = new google.maps.Map(document.getElementById("map-left-prior"), mapOptions_prior);
    map_over_lhs    = new google.maps.Map(document.getElementById("map-left-latest"), mapOptions_latest);
    map_rhs               = new google.maps.Map(document.getElementById("map-right"), mapOptions_prior);
    
    if (single_map == true){
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
    
    var share = area_json['properties']['shared']; //$('#area_share').text(); 
    
    if (share == 'public')
    {
        $("#public").prop("checked", true)          
    }
    else if (share == 'unlisted')
    {
        $("#unlisted").prop("checked", true)          
    }
    else    if (share == 'private')
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
    
    
    boundary_coords_str = '<p class="divider small">'
    var coords_arr   =  area_json['features'][1]['geometry']['coordinates'];  // init global.

    //console.log(coords_arr);
    
    for (j=0; j < coords_arr.length; j++)
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
    areaBoundary_over_lhs = new google.maps.Polygon({
                paths: border_latlngs,
                strokeColor: '#FFFF00',
                strokeOpacity: 0.5,
                strokeWeight: 2,
                fillColor: '#000000',
                fillOpacity: 0.05
    });
    
    areaBoundary_under_lhs= new google.maps.Polygon({
                paths: border_latlngs,
                strokeColor: '#FFFF00',
                strokeOpacity: 0.5,
                strokeWeight: 2,
                fillColor: '#000000',
                fillOpacity: 0.05
    });
    
    areaBoundary_rhs = new google.maps.Polygon({
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
    overlayMaps.push(areaBoundary_over_lhs);
    
    addLayer(areaBoundary_over_lhs.name, area_json['properties']['area_name'] +" Border", "yellow",  50, "Boundary of Area " + area_json['properties']['area_name'], layerslider_callback);
      
    /*  if AOI is new, then need to ask earthengine to calculate what cells overlap the areaAOI. 
     *  This is done here the first time the area is viewed. But could be part of constructor for AreaOfInterest.
     */    
    cellarray = jQuery.parseJSON($('#celllist').text()); 
  
    var jobid = -1;

    
    $('#close-dialog-new-cells').click(function(){    
        $('#dialog-new-cells').popoverX('hide');
    }); 

    $('#close-dialog-new-cells-open-accordion').click(function(){
        $('#cell_panel_title').collapse('show');       //open  cell_panel_title
        $('#dialog-new-cells').popoverX('hide');
   }); 
    
    if(cellarray.length == 0) { // Then fetch the overlapping cells from server.
        console.log("Init: Fetching Overlapping Cells for Area");
        var url = area_json['properties']['area_url'] + '/getcells';
        
        $('#cell_panel_title').collapse('show');       //open  cell_panel_title to set height.
        
        $('#dialog-new-cells').popoverX({
            target: '#cell_panel_t'  //container
        });
        $('#dialog-new-cells').popoverX('show');
        setTimeout(function() {
            $('#dialog-new-cells').popoverX('hide');
        }, 80000);
		
        prompt = "<h6><small>Calculating Cells</small></h6><img src='/static/img/ajax-loader.gif' class='ajax-loader'/>";
        jobid = addJob(prompt, 'gray');
      
        $.get(url).done(function(data) {
                        
            var getCellsResult = jQuery.parseJSON(data);
            
            if (getCellsResult.result == 'success'){
                cellarray = getCellsResult.cell_list;
                console.log('GetCells result: ' + getCellsResult.result + ' reason: ' + getCellsResult.reason);
         
                var plurals = (cellarray.length == 1)? ' cell covers': ' cells cover';
                var plurals_mon = (getCellsResult.monitored_count == 1)? ' cell selected': ' cells selected';
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
    
    observations = jQuery.parseJSON($('#obslist').text());
    for (i=0; i < observations.length; i++) {        
        displayObsOverlay(observations[i], 'latest', 'rgb'); //LHS overlay(s)
        displayObsOverlay(observations[i], 'prior', 'rgb'); //RHS overlays(s)        
     }
 
    // View button will fetch Latest Overlay Image of selected (last clicked) cell on LHS.
    $('#get_overlay_btn').click(function(){
        requestAdHocOverlay();
        
    }); //get_overlay_btn.click

    $('#make_report').click(function(){
        drawingManager  = createDrawingManager(map_over_lhs)
        $('#make_report').popoverX({
            target: '#cell_panel_t'  //container
            content: 'sign in'
        });
        google.maps.event.addListener(drawingManager, 'overlaycomplete', function(event) {
                    href = '/' + area_json['properties']['owner'] + '/journal/Observations for ' + area_json['properties']['area_name'] + '/new';
                    window.location.href = href; //+ mapobj.id;
                });
     });

    $('#sign_in').click(function(){
        $('#make_report').popoverX({
            target: '#cell_panel_t'  //container
        });
     });
   
    //Change the text in the drop-down button when a selection is changed.
    $('#algorithm-visual').click(function(e){
           $("#algorithm:first-child").text("RGB");
           algorithm = 'rgb';
           e.preventDefault();
        });
        $('#algorithm-ndvi').click(function(e){
           $("#algorithm:first-child").text("NDVI");
           algorithm = 'ndvi';
           e.preventDefault();
        });
        $('#algorithm-change').click(function(e){
           $("#algorithm:first-child").text("Change");
           algorithm = 'change';
           e.preventDefault();
        });
        
        $('#latest').click(function(e){
            $("#latest:first-child").text("Latest  ");
            latest = 0;
            e.preventDefault();
        });
        $('#latest-1').click(function(e){
            $("#latest:first-child").text("Latest-1");
            latest = 1;
            e.preventDefault();
        });
        $('#latest-2').click(function(e){
            $("#latest:first-child").text("Latest-2");
            latest = 2;
            e.preventDefault();
        });
        $('#latest-3').click(function(e){
            $("#latest:first-child").text("Latest-3");
            latest = 3;
            e.preventDefault();
        });
        
        $('#satellite').click(function(e){
            $("#satellite:first-child").text("L8");
            satellite = 'l8';
            e.preventDefault();
        });
        $('#satellite-l7').click(function(e){
            $("#satellite:first-child").text("L7");
            satellite = 'l7';
            e.preventDefault();
        });
        $('#satellite-both').click(function(e){
            $("#satellite:first-child").text("Both");
            satellite = 'l78';
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

        $('#instructions').popover({ 
            html : true, 
            animation: true,
            trigger: 'hover',
            container: 'body',
            title: 'Manage Area',  
            placement: 'bottom',
            footer: "OK",
            content:  "The square white cells overlapping your area are the outlines of Landsat images<br/><br/>" + 
            "Monitored cells are highlighted with a bolder line.<br/><br/>" + 
            "Change which cells are monitored with the <a id='close-dialog-new-cells-open-accordion'><i>Landsat Cells</i></a> controls below.<br/><br/>" + 
            "Change the default view for your area with the Map panel.<br/><br/>" +
            "Change whether your area can be seen by other users with the sharing controls under Area.<br/><br/>" 
            });
        
        $('#save-view').popover({ 
            html : true, 
            animation: true,
            trigger: 'hover',
            container: 'body',
            title: 'Save View',  
            placement: 'bottom',
            content: save_view_instructions
            });
        
        $('#reset-view').popover({ 
            html : true, 
            animation: true,
            trigger: 'hover',
            container: 'body',
            title: 'Reset View',  
            placement: 'bottom',
            content: reset_view_instructions
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
  
        $('#dragger').draggable({
            axis: 'x',
            containment: 'parent',
            /*handle: '#draghandle',*/
            cursor: 'col-resize',
            drag: function(e, u) {
              var left = u.position.left;
              $('#map-left-c-prior').width(left);
              //$('#draghandle').width('11px').height('11px');
            }
        });
        
        $("#map-left-c-prior").on({
            mousemove: function(e){
                x = e.pageX - lhs_offset_left;
                y = e.pageY - lhs_offset_top;
                $("#rhs_cursor").css({left: x, top: y})
            }
        });
        
        $("#map-left-c-latest").on({
            mousemove: function(e){
                x = e.pageX - lhs_offset_left;
                y = e.pageY - lhs_offset_top;
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
    
        $('#edit-cells-lock').click(function(e){
            toggle_edit_cells_lock();
        });
        toggle_edit_cells_lock();  // call during init to draw div
        
        $('#delete_area_id').click(function(e) {
            
                bootbox.dialog({
                      message: "<b>Warning!</b> Deleting this area cannot be undone.<br/>Data contained with the area will also be deleted.<br/>Volunteers who follow this area will be notified.",
                      title: "Delete Area <b>" + area_json['properties']['area_name']+  "</b> - Are You Sure?",
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
                              window.location.href =  area_json['properties']['area_url']  + "/delete" ;
                          }
                        }
                      }
                    });
            }     
        );//delete-are-you-sure handler
};//initialize

function httpgetActionUrl(action)
{
   // action/<action> can be 'overlay' or 'download' or image.
   //TODO: satellite is 'l8' or 'l7' but should change to collection name.
   //TODO: latest is still a global var....
   var satellite = $("#satellite:first-child").text().trim();
   var algorithm = $("#algorithm:first-child").text().trim();
   var path = map_over_lhs.landsatGridOverlay.selectedPath;
   var row  = map_over_lhs.landsatGridOverlay.selectedRow;

   var url =  area_json['properties']['area_url']  + '/action/' + action + '/' + satellite + '/' + algorithm + '/' + latest;
  
   if((path != -1) && (row != -1))
   {
       url  += "/" + path + "/" + row;
   }
   return url
};

function ajaxActionUrl(action)
{
   // action can be 'overlay' or 'download'.
   url =  area_json['properties']['area_url']   + '/action/' + satellite + '/' + algorithm + '/' + latest;
   return url
};


function drawLandsatCells(cellarray) {
    createLandsatGridOverlay(map_over_lhs, 0.5, true, cellarray);
    addLayer( map_over_lhs.landsatGridOverlay.name,
            'Landsat Cells',
            'gray',  
            75, 
            "Each Landsat image covers one of these cells.", 
            layerslider_callback ); //create slider.
}


// update_map_panel updates the panel div based on values of the map after bounds changed event.

function update_map_panel(map, panel) {       
    htmlString = "<span class=divider small><strong>zoom:</strong>   " + map.getZoom() + " <br/>";
    //htmlString += "<strong>center:</strong><br>";
    htmlString += "Center(" + map_under_lhs.getCenter().lat().toFixed(3) + ",  " + map_under_lhs.getCenter().lng().toFixed(3) + ")</span>";
    $(panel).empty().html(htmlString); 
};


//update_map_cursorupdates the panel div with values of the cursor in long based after map becomes idle.

function update_map_cursor(map, pnt, panel) {   
    var lat = pnt.lat();
    lat = lat.toFixed(4);
    var lng = pnt.lng();
    lng = lng.toFixed(4);
    var htmlString  = "Cursor( " + lat + ", " + lng + ")";
    $(panel).html(htmlString); 
};
    
    
