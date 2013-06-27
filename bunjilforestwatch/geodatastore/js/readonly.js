geodatastore.mapDisplay = function(id) {
  this.map_ = null;
  this.dom_ = {
    wrapper_div: document.getElementById(id),
    sidebar_divs: []
  }
  this.selected_geometry_ = null;
  this.geometries_ = [];
  this.createMap_();
};

geodatastore.mapDisplay.prototype.createMap_ = function() {
  var me = this;

  var created_divs = geodatastore.createMapWithSidebar(this.dom_.wrapper_div);
  this.dom_.map_div = created_divs.map_div;
  this.dom_.sidebar_div = created_divs.sidebar_div;
 
  this.map_ = new GMap2(this.dom_.map_div); 
  this.map_.setCenter(new GLatLng(37, -122));
  this.map_.addControl(new GLargeMapControl());
  this.map_.addControl(new GMapTypeControl());
  this.map_.enableGoogleBar();

  // Create a base icon for all of our markers that specifies the
  // shadow, icon dimensions, etc.
  var icon = new GIcon(G_DEFAULT_ICON);
  icon.image = 'http://gmaps-samples.googlecode.com/svn/trunk/markers/green/blank.png';
  icon.shadow = "http://www.google.com/mapfiles/shadow50.png";
  icon.iconSize = new GSize(20, 34);
  icon.shadowSize = new GSize(37, 34);
  icon.iconAnchor = new GPoint(9, 34);
  icon.infoWindowAnchor = new GPoint(9, 2);
  icon.infoShadowAnchor = new GPoint(18, 25);
  this.icon_ = icon;

  this.loadKmlData_();
};

geodatastore.mapDisplay.prototype.updateHighlightPoly_ = function() {
  var me = this;
  if (me.highlightPoly_) { me.map_.removeOverlay(me.highlightPoly_); }
  if (!me.selected_geometry_) { return; }
  if (me.selected_geometry_.data.type == 'point') {
    var latlng = me.selected_geometry_.getLatLng();
    var span = me.map_.getBounds().toSpan();
    var half_lat = span.lat() * .05;
    var half_lng = span.lng() * .05;
    var latlngs = [new GLatLng(latlng.lat() - half_lat, latlng.lng() - half_lng),
                   new GLatLng(latlng.lat() - half_lat, latlng.lng() + half_lng),
                   new GLatLng(latlng.lat() + half_lat, latlng.lng() + half_lng),
                   new GLatLng(latlng.lat() + half_lat, latlng.lng() - half_lng),
                   new GLatLng(latlng.lat() - half_lat, latlng.lng() - half_lng)];
  } else {
    if (!me.selected_geometry_.hasEnded) return;
    var bounds = me.selected_geometry_.getBounds();
    var span = me.map_.getBounds().toSpan();
    var half_lat = 0;
    var half_lng = 0;
    var latlngs = [new GLatLng(bounds.getNorthEast().lat() - half_lat, bounds.getSouthWest().lng() - half_lng),
                   new GLatLng(bounds.getNorthEast().lat() - half_lat, bounds.getNorthEast().lng() + half_lng),
                   new GLatLng(bounds.getSouthWest().lat() + half_lat, bounds.getNorthEast().lng() + half_lng),
                   new GLatLng(bounds.getSouthWest().lat() + half_lat, bounds.getSouthWest().lng() - half_lng),
                   new GLatLng(bounds.getNorthEast().lat() - half_lat, bounds.getSouthWest().lng() - half_lng)];
  }
  var color = me.selected_geometry_.isEdited ? '#FF0000' : '#FF8921';
  me.highlightPoly_ = new GPolygon(latlngs, '#ff0000', 0, 0.0, color, 0.2, {clickable: false});
  me.map_.addOverlay(me.highlightPoly_);
};
    
geodatastore.mapDisplay.prototype.createSidebarEntry_ = function(geometry) {
  var me = this;
  var div = document.createElement('div');
  div.style.cursor = 'pointer';
  div.style.marginBottom = '5px'; 

  div.className = 'viewable_div';
  div.innerHTML = '';
  var view_div = me.createView_(geometry, div);
  div.appendChild(view_div);
  return div;
};

geodatastore.mapDisplay.prototype.createTableRow_ = function(label, value, is_input, geometry) {
  var tr = document.createElement('tr');
  var label_td = document.createElement('td');
  label_td.className = 'view_label';
  label_td.appendChild(document.createTextNode(label + ': '));
  var value_td = document.createElement('td');
  if (is_input) {
    var value_input = document.createElement('input');
    value_input.type = 'text';
    value_input.value = value;
    value_input.id = label.toLowerCase() + '_input';
    value_td.appendChild(value_input);
  } else {
    value_td.appendChild(document.createTextNode(value));
  }
  tr.appendChild(label_td);
  tr.appendChild(value_td);
  return tr;
};

geodatastore.mapDisplay.prototype.createView_ = function(geometry, parent_div) {
  var me = this;
 
  var div = document.createElement('div');
  var table = document.createElement('table');
  var tbody = document.createElement('tbody');
  tbody.appendChild(me.createTableRow_('Name', geometry.data.name, false, geometry));
  tbody.appendChild(me.createTableRow_('Description', geometry.data.description, false, geometry));
  table.appendChild(tbody);
  div.appendChild(table);
  return div;
};

geodatastore.mapDisplay.prototype.loadKmlData_ = function() {
  var me = this;
  var url_base = 'gen/';
  var url = url_base + 'request?operation=get&output=json';
  GDownloadUrl(url, function(data, responseCode) { me.handleDataResponse_(me, data, responseCode); });
};


geodatastore.mapDisplay.prototype.handleDataResponse_ = function(me, data, responseCode) {
  if (responseCode == 200) {
    var json_data = eval('(' + data + ')');
    if (json_data.status != 'success') return;
    switch (json_data.operation) {
      case 'get':
        var geometries = json_data.result.geometries;
        var bounds = new GLatLngBounds();
        for (var i = 0; i < geometries.records.length; i++) {
          var record = geometries.records[i];
          var geometry = me.createGeometry_(record);
          if (record.type == 'point') {
            bounds.extend(geometry.getLatLng());
          } else if (record.type == 'line' || record.type == 'poly') {
            bounds.extend(geometry.getBounds().getCenter());
          }  
        }
        if  (!bounds.isEmpty() && geometries.records.length > 1) {
          me.map_.setCenter(bounds.getCenter());
          me.map_.setZoom(me.map_.getBoundsZoomLevel(bounds));
        }
    }
  }
};


geodatastore.mapDisplay.prototype.createGeometry_ = function(data, is_editable) {
  var me = this;
  if (data.type == 'point') {
    var geometry = new GMarker(new GLatLng(data.coordinates[0].lat,
    data.coordinates[0].lng), {icon: me.icon_});
  } else if (data.type == 'line' || data.type == 'poly') {
    var latlngs = [];
    for (var i = 0; i < data.coordinates.length; i++) {
      latlngs.push(new GLatLng(data.coordinates[i].lat, data.coordinates[i].lng));
    }
    var geometry = (data.type == 'line') ? new GPolyline(latlngs) : new GPolygon(latlngs, '#0000ff', 2, 0.7, '#0000ff', 0.2);
  }
  geometry.data = data;

  var sidebar_entry = me.createSidebarEntry_(geometry);
  me.dom_.sidebar_div.appendChild(sidebar_entry);
  geometry.sidebar_entry = sidebar_entry;
  this.map_.addOverlay(geometry);
  this.geometries_.push(geometry);

  GEvent.addListener(geometry, 'click', function() {
    me.selected_geometry_ = geometry;
    me.updateHighlightPoly_();
  });

  return geometry;
};
 
