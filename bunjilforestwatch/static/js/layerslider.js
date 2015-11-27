/* layerslider allows you to add an array of nouisliders to a div called #LayerTemplate*/

var callbacks = $.Callbacks();


function setLayerOpacity(e) {  
    //console.log("setLayerOpacity");
    var slider = $(this);
    var val = slider.val();
    var layername = slider.context.id.substr(7); //strip "slider_"
    var checkbox_id = "#checkbox_" + layername;
    
    callbacks.fire(layername, val);
    
    // toggle the check box.
    var checkbox = $(checkbox_id); //could be a quicker search.
    if (val === 0) {
       checkbox.prop('checked', false);
    }
    else {
      checkbox.prop('checked', true);
    }
}

function toggleLayer(e){
  var checkbox = $(this);
  
  var val;
  if ( checkbox.is(':checked') ) {
	 val = 100;
  }
  else {
     val = 0;
  }
  var slider = checkbox.parent().parent().find(".slider");    
  slider.val(val);
  
  var layername = slider.context.id.substr(9); //strip "checkbox_"
  callbacks.fire(layername, val);
}


function addLayer(layer_id, layer_name,  slider_color, slider_value, tooltip, callback) {
    
    var newDiv = $("#LayerTemplate").clone();
    if (newDiv === 'undefined') {
    	console.log("missing panel div in HTML");
    	return;
    }
    // This id should be different for each instance.
    newDiv.attr("id", layer_id);
    newDiv.id=layer_id;
  
    newDiv.find("#tlabel_id").html("<h6><small>" + layer_name +
                            "</small></h6>").attr("id", "label_" + layer_id).attr("title", tooltip);
  
    var checkbox=newDiv.find("#tcheckbox_id"); 
    if(slider_value === 0)
    {
         checkbox.prop("checked", false);
    }
    var checkbox_id = "checkbox_" + layer_id;
    checkbox.attr("id", checkbox_id);
    
    checkbox.click( toggleLayer);
   
    var slider = newDiv.find("#tslider_id");
    slider.noUiSlider({
        start: slider_value,
        connect:"lower",
        range: {    
            'min': 0,
            'max': 100
        },
        step: 5
    });
    slider.css({
		background: slider_color,
		color: slider_color
	});
    
    var slider_id = "slider_" + layer_id;
    slider.attr("id", slider_id);
 
    if (typeof callback === 'function') {   
        if ( callbacks.has(callback) === false)
        {    
            //console.log("adding slider callback: " + callback);
            callbacks.add( callback );
        }
    }
    slider.on('change', setLayerOpacity);// this will also call the supplied callback
    newDiv.show();
    $("#layer_table").append(newDiv);
 }
    
 
function test_callback(layer_id, val) {
    console.log("test_callback : " + layer_id + ", " + val);
}

/* EXAMPLE USAGE 
function unit_test_sliderlayer() {
    //create a test case array of sliders.
    addLayer("1", "1st name", "red",  0, "first tooltip", test_callback);
    addLayer("2", "2nd name", "green",100, "second tooltip");
    addLayer("3", "3rd name", "blue", 100, "third tooltip", test_callback);   
    addLayer("funnyname", "4th name", "cyan", 100, "funny tooltip", test_callback);   
}
*/
