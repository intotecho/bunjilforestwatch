

var map_under_lhs; //side by side maps
var map_over_lhs; //side by side maps
var map_rhs;

var satellite = 'l8'
var algorithm = 'rgb'; // ndvi 
var latest = 0;  //latest - 0
var overlayMaps = [];

var latlngs = [];
var boundary_coords= "";


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
   return url
};


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
                 }
   return JSON.stringify(cell_feature);
};

function cellSelected(landsat_cell)
{
// Fetch Outline and status of this Landsat Cell

  var httpget_url = "/selectcell/" + area_url + "/" + jsonStringifySelectedCell(landsat_cell)
  console.log( "cellSelected() %d %d %s", landsat_cell.path, landsat_cell.row, httpget_url);
   
  $("#ee_panel").collapse('show');
       $('#ee_panel').empty();
       $('#ee_panel').append("SelectCell...");
       $('#ee_panel').append('<img src="/static/img/ajax-loader.gif" class="ajax-loader"/>');
       $.get(httpget_url).done(function(data) {
              $('#ee_panel').empty();
              var panel_str = "Cell:"          
              var celldict = jQuery.parseJSON(data);
              console.log(celldict)
              if (celldict['result'] == "ok") {                                           
                  if (celldict.monitored == "true") 
                      {
                        panel_str = "Now Monitoring Cell(" + celldict.path  + ", " +  celldict.row + ")<br>Last Obs: " + celldict.LC8_latest_capture;
                        console.log( "Following: " + celldict.path  + ", " +  celldict.row)
                        landsat_cell.Monitored = true;
                        monitor_cell(landsat_cell, landsat_cell.Monitored);
                      }
                  else
                      {
                         panel_str = "Stopped Monitoring Cell(" + celldict.path  + ", " +  celldict.row + ") ";
                         console.log( "Stopped Monitoring: " + celldict.path  +", " +  celldict.row)
                         landsat_cell.Monitored = false;
                         monitor_cell(landsat_cell, landsat_cell.Monitored);
                      }
                  $('#ee_panel').append(panel_str);  
               }
               else {
                   console.log( "Error: " + celldict['result']);
               }             
        }).error(function( jqxhr, textStatus, error ) {
            var err = textStatus + ', ' + error;
            console.log( "Request Failed: " + err);
            $('#ee_panel').empty();
            $('#ee_panel').append("<p>Failed: " + err + "</p>"); 
     });
}

