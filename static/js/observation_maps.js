function initialize(oldTLLat, oldTLLon, oldBRLat, oldBRLon, newTLLat, newTLLon, newBRLat, newBRLon, oldImage, newImage) {
    var oldImageBounds = new google.maps.LatLngBounds(
        new google.maps.LatLng(oldTLLat,oldTLLon),
        new google.maps.LatLng(oldBRLat,oldBRLon));
    var newImageBounds = new google.maps.LatLngBounds(
        new google.maps.LatLng(newTLLat,newTLLon),
        new google.maps.LatLng(newBRLat,newBRLon));
    var leftMapOptions = {
        center: oldImageBounds.getCenter(),
        zoom: 6,
        mapTypeId: google.maps.MapTypeId.SATELLITE 
    };
    var rightMapOptions = {
        center: newImageBounds.getCenter(),
        zoom: 6,
        mapTypeId: google.maps.MapTypeId.SATELLITE 
    };

    var left_map = new google.maps.Map(document.getElementById("left_map_canvas"), leftMapOptions);
    var right_map = new google.maps.Map(document.getElementById("right_map_canvas"), rightMapOptions);
    var oldMapOverlay = new google.maps.GroundOverlay(
        oldImage,
        oldImageBounds,
        {
            clickable: false,
            map: left_map
        });
    var newMapOverlay = new google.maps.GroundOverlay(
        newImage,
        newImageBounds,
        {
            clickable: false,
            map: right_map
        });
    google.maps.event.addListener(left_map, 'center_changed', function() {
        right_map.panTo(left_map.getCenter());
    });
    google.maps.event.addListener(right_map, 'center_changed', function() {
        left_map.panTo(right_map.getCenter());
    });
    google.maps.event.addListener(left_map, 'idle', function() {
        right_map.setZoom(left_map.getZoom());
    });
    google.maps.event.addListener(right_map, 'idle', function() {
        left_map.setZoom(right_map.getZoom());
    });
    google.maps.event.addListener(right_map, 'click', function(event) {
        var marker = new google.maps.Marker({
            position: event.latLng,
            map: right_map
        });
        var tag = document.createElement("input");
        var form = document.getElementById("new_report");
        tag.type = "hidden";
        tag.id = "report_location";
        tag.name = "report[location][]";
        tag.value = event.latLng.toUrlValue();
        form.appendChild(tag);
        google.maps.event.addListener(marker, 'click', function() {
            marker.setMap(null);
            form.removeChild(tag);
        });
    });
}