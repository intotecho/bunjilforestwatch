/*******************************************************************************
 * Copyright (c) 2014 Chris Goodman GPLv2 Creative Commons License to share
 * See also https://developers.google.com/maps/documentation/javascript/examples/overlay-hideshow
 ******************************************************************************/
var overlayMaps = [];

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
        
        overlayMaps[id].setOpacity(Number(val)/100);
    }
}


function removeFromMap(map, overlay_id)
{
    //TODO: hide slider
    //overlay = overlayMaps.pop(); //needs to be a splice not a pop.
    //overlay.hide();
}

