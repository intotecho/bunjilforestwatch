//Depends on readonly.js

geodatastore.mapDisplay.prototype.locator_override_createMap_ = 
  geodatastore.mapDisplay.prototype.createMap_;

geodatastore.mapDisplay.prototype.loadKmlData_ = function() {};

geodatastore.mapDisplay.prototype.createMap_ = function(id) {
  var me = this;
  if (!this.geocoder_) {
    this.geocoder_ = new GClientGeocoder();
  }
  this.locator_override_createMap_(id);
  this.map_.setCenter(new GLatLng(39.88, -96.8), 4);
  this.map_.disableGoogleBar();
  
  var input_div = document.createElement('div');
  input_div.style.padding = '10px';
  var search_box_div = document.createElement('div');
  var search_box = document.createElement('input');
  search_box.id = 'search_box';
  search_box.type = 'text';
  search_box_div.appendChild(search_box);
  var search_button_div = document.createElement('div');
  var search_button = document.createElement('input');
  search_button.type = 'button';
  search_button.value = 'Search';
  search_button_div.appendChild(search_button);
  input_div.appendChild(search_box_div);
  input_div.appendChild(search_button_div);
  
  GEvent.addDomListener(search_button, 'click', function() {
    var jsonScript = document.getElementById('jsonScript');
    if (jsonScript) {
      jsonScript.parentNode.removeChild(jsonScript);
    }
    
    var search_box = document.getElementById('search_box');
    me.geocoder_.getLatLng(search_box.value, function(location) {
      if (location == null) {
        alert('Unable to find location');
      } else {
        var src = '/locate?lat=' + location.lat();
        src += '&lon=' + location.lng();
        src += '&num=3&alt=json-in-script';
        src += '&callback=geodatastore.mapDisplay.handleLocatorJson';
      
        var script = document.createElement('script');
        script.setAttribute('src', src);
        script.setAttribute('id', 'jsonScript');
        script.setAttribute('type', 'text/javascript');
        
        document.documentElement.firstChild.appendChild(script);
      }
    });
  });
  
  this.dom_.sidebar_div.appendChild(input_div);
  window.geodatastore_object_ = this;
};

geodatastore.mapDisplay.handleLocatorJson = function(json) {
  window.geodatastore_object_.map_.clearOverlays();
  var records = json.result.geometries.records;
  var bounds = new GLatLngBounds();
  for (var i=0; i<records.length; i++) {
    var lat = records[i].coordinates[0].lat;
    var lng = records[i].coordinates[0].lng;
    var loc = new GLatLng(lat, lng);
    
    bounds.extend(loc);
    
    var marker = new GMarker(loc);
    marker.bindInfoWindowHtml(records[i].description);
    window.geodatastore_object_.map_.addOverlay(marker);
  }
  if (!bounds.isEmpty()) {
    window.geodatastore_object_.map_.setCenter(bounds.getCenter());
    window.geodatastore_object_.map_.setZoom(window.geodatastore_object_.map_.getBoundsZoomLevel(bounds));
  }
};
