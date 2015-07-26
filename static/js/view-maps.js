var map_under_lhs; //side by side maps
var map_over_lhs; //side by side maps
var map_rhs;

var map_center;
var map_zoom;

var satellite = 'l8'
var algorithm = 'rgb'; // ndvi 
var latest = 0;  //latest - 0
var overlayMaps = [];

var save_view_instructions = 
    "Save the current view.<br/>" +
    "All users will see this as the initial view when they open an observation for this area. <br/>" ;
    
var reset_view_instructions = 
        "Return map to the initial view.<br/>" +
        "This does not update the saved view.<br/>" ;

function setActionUrl(action)
{
   // action can be 'overlay' or 'download' strip the old action and append the new action.
   var url = window.location.href
   if (url.indexOf("/overlay") !=-1) {
      url = url.substring(0, url.indexOf("/overlay")); //strip the last action.
   }
   if (url.indexOf("/download") !=-1) {
       url = url.substring(0, url.indexOf("/download")); //strip the last action.
   }
   if (url.indexOf("/action") !=-1) {
          url = url.substring(0, url.indexOf("/action")); //strip the last action.
    }

   url = url + '/action/' + action + '/' + satellite + '/' + algorithm + '/' + latest;
   
   //Not working so disable the final bit.
   return url;
}


function jsonStringifySelectedCell(landsat_cell)
{
   var ul=[landsat_cell.selectedLAT_UL, landsat_cell.selectedLON_UL]; //TODO: move these from global to cell 
   var ll=[landsat_cell.selectedLAT_LL, landsat_cell.selectedLON_LL];
   var lr=[landsat_cell.selectedLAT_LR, landsat_cell.selectedLON_LR];
   var ur=[landsat_cell.selectedLAT_UR, landsat_cell.selectedLON_UR];
   
   var cell_coords = Array();
   
   cell_coords.push(ul);
   cell_coords.push(ll);
   cell_coords.push(lr);
   cell_coords.push(ur);
  
   var cell_feature = { "type": "Feature",
            "geometry":   {"type": "Polygon","coordinates": cell_coords},
            "properties": {"featureName": "cell_boundary", "path": landsat_cell.path, "row": landsat_cell.row}
                 };
   return JSON.stringify(cell_feature);
}

//modify area with new value of shared.
function updateAreaShared(shared)
{
  var url =  area_json['properties']['area_url'] + "/update/share/" + shared;
  var result;
  console.log( "updateAreaShared() url:%s", url);

  var xhr = $.post(url).done(function(data) {
			console.log ('done. updated area.shared: ' + data);
			$('#area_sharing_heading').html("Sharing: "+ data);
 			return data;
 			
	}).error(function(xhr, textStatus, error){
			  console.log ('updateAreaShared() request failed:', xhr.status, error);
			  $('#area_sharing_heading').html("Sharing Update error");
			  return error;
		});
}

$('#save-view').click(function(){
	
	var map = map_under_lhs;
	var url =  area_json['properties']['area_url'] + '/update/view?lat=' + map.getCenter().lat().toFixed(5)+ '&lng=' + map.getCenter().lng().toFixed(5) + '&zoom=' + map.getZoom();
	console.log('save-view:', url);

	var xhr = $.post(url).done(function(data) {
		  $('#map_panel_center').empty().append("<p>Saved</p>"); 
			return data;
			
	}).error(function(xhr, textStatus, error){
			  console.log ('UpdateAreaView() request failed:', xhr.status, error);
			  $('#map_panel_center').empty().append("<p>UpdateAreaView Failed: " + error + "</p>"); 
			  return error;
	});
});


$('#reset-view').click(function(){
	console.log('reset-view:');
	var map = map_under_lhs;
    map.setZoom(map_zoom);
    map.setCenter(map_center);
});

var monitored_cells_are = 
	"<b>Monitored</b> cells are highlighted with a bolder outline. " + 
	"Only <b>Monitored</b> cells generate new observation tasks which are " +
	"sent to the area\'s followers when new images are found. <br/>";

var edit_cells_instructions_editing = 
	"Now <b>Editing Cells</b>. Swap any cell between monitored and unmonitored by clicking it.<br/>" +
	"When finished, click <span class='glyphicon glyphicon-edit cell-panel-popover-edit'/> to prevent further changes.<br/><br/>" +
	monitored_cells_are;

var edit_cells_instructions_locked = 
    "While <b>Locked</b>, cells won't change when you click them. <br/>" +
    "Click <span class='glyphicon glyphicon-edit cell-panel-popover-locked'/> to <b>Edit cells</b>.<br/><br/>" +
     monitored_cells_are;

function toggle_edit_cells_lock()
{
	edit_cells_mode = ! edit_cells_mode; //toggle editing.
    
	var panel = $('#edit-cells-lock'); 
	if (panel.length) //only exists if user is owner...
	{
		console.log("Edit Cells Lock: ", edit_cells_mode);
		panel.popover({ 
		    html : true, 
		    animation: true,
		    trigger: 'hover',
		    container: 'body',
		    placement: 'right',
		 });
		
		var popover = panel.data('bs.popover');
		
		if (edit_cells_mode) {
			panel.html("<span class='glyphicon glyphicon-edit cell-panel-popover-edit'/><span class='cell-panel-info'> Editing Cells<span>");
		    popover.options.content = edit_cells_instructions_editing;
		    popover.options.title = "<span class='cell-panel-popover-edit'> Editing Monitored Cells</span>";
			
		}
		else {
			panel.html("<span class='glyphicon glyphicon-lock cell-panel-popover-locked'/><span class='cell-panel-info'> Locked (Click to edit cells)<span>");
		    popover.options.content = edit_cells_instructions_locked;
		    popover.options.title = "<span class='cell-panel-popover-locked'> Cell editing is Locked</span>";
		}
	
	    if ( typeof toggle_edit_cells_lock.staticPropertyinit == 'undefined' ) {
	        //console.log("First Call - Init Edit Cells Lock");
	        toggle_edit_cells_lock.staticPropertyinit = 0;
		}
	    else {
	    	panel.popover('show');    
	    }
	}   
}
