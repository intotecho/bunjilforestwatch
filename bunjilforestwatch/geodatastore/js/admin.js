geodatastore.adminPanel = function(id) {
  this.map_ = null;
  this.dom_ = {
    wrapper_div: document.getElementById(id),
    sidebar_divs: []
  }
  this.selected_geometry_ = null;
  this.geometries_ = [];
  this.mode_ = 'view';
  this.createMap_();
};

geodatastore.adminPanel.prototype.canUserEdit_ = function(userId) {
  return (userId == current_user || is_admin == 'True'); 
}

geodatastore.adminPanel.prototype.isUserLoggedIn_ = function() {
  return current_user != 'Not logged in';
}

geodatastore.adminPanel.prototype.createMap_ = function() {
  var me = this;

  var created_divs = geodatastore.createMapWithSidebar(this.dom_.wrapper_div);
  this.dom_.map_div = created_divs.map_div;
  this.dom_.sidebar_div = created_divs.sidebar_div;

  this.map_ = new GMap2(this.dom_.map_div, {googleBarOptions:
  {showOnLoad: true, onGenerateMarkerHtmlCallback : function(marker, html, result) {
    return me.extendMarker_(me, marker, html, result);}}});
  this.map_.setCenter(new GLatLng(37, -122));
  this.map_.addControl(new GLargeMapControl());
  this.map_.addControl(new GMapTypeControl());
  this.map_.enableGoogleBar();

  if (this.isUserLoggedIn_()) {
    var edit_control = new EditControl();
    this.map_.addControl(edit_control);
    var status_control = new StatusControl();
    this.map_.addControl(status_control);
  
  GEvent.addListener(edit_control, 'view', function() {
    me.mode_ = 'view';
    status_control.setText('Select geometries by clicking on them.');
  });
  GEvent.addListener(edit_control, 'point', function() {
    me.mode_ = 'point';
    status_control.setText('Click on the map to create a new marker.');
  });
  GEvent.addListener(edit_control, 'line', function() {
    me.mode_ = 'line';
    status_control.setText('Click on the map to start creating a new line.');
  });
  GEvent.addListener(edit_control, 'poly', function() {
    me.mode_ = 'poly';
    status_control.setText('Click on the map to start creating a new filled poly.');
  });
  }
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
  this.icons_ = {};
  this.icons_.unchanged = new GIcon(icon);
  this.icons_.unchanged.image = 'http://gmaps-samples.googlecode.com/svn/trunk/markers/blue/blank.png';
  this.icons_.newlysaved = new GIcon(icon);
  this.icons_.newlysaved.image = 'http://gmaps-samples.googlecode.com/svn/trunk/markers/orange/blank.png';
  this.icons_.notsaved = new GIcon(icon);
  this.icons_.notsaved.image = 'http://gmaps-samples.googlecode.com/svn/trunk/markers/red/blank.png';

  GEvent.addListener(this.map_, 'click', function(overlay, latlng) {
    // todo check if we're already editing something
    if (me.mode_ == 'view' || (me.selected_geometry_ && !me.selected_geometry_.hasEnded)) {
      return;
    }
    if (overlay) return; 
    new_geometry_data = {};
    new_geometry_data.name = '';
    new_geometry_data.description = '';
    new_geometry_data.userId = current_user;
    new_geometry_data.coordinates = [];
    new_geometry_data.coordinates.push({lat: latlng.lat(), lng: latlng.lng()});
    new_geometry_data.type = me.mode_;
    var new_geometry = me.createGeometry_(new_geometry_data, true); 
    if (me.mode_ == 'point') GEvent.trigger(new_geometry, 'click');
  });
  GEvent.addListener(this.map_, 'zoomend', function() {
    me.updateHighlightPoly_();
  });
  this.loadKmlData_();
};

geodatastore.adminPanel.prototype.extendMarker_ = function(gs, marker, html, result) {
  var me = this;
  // extend the passed in html for this result
  // http://code.google.com/apis/ajaxsearch/documentation/reference.html#_class_GlocalResult
  if (!me.isUserLoggedIn_()) return; 
  var div = document.createElement('div');
  var button = document.createElement('input');
  button.type = 'button';
  button.value = 'Create copy on map';
  button.onclick = function() {
    var new_geometry_data = {};
    new_geometry_data.name = result.titleNoFormatting;
    new_geometry_data.description = result.streetAddress;
    new_geometry_data.userId = current_user;
    new_geometry_data.fromGoogleBar = true;
    new_geometry_data.type = 'point';
    new_geometry_data.coordinates = [];
    new_geometry_data.coordinates.push({lat: marker.getLatLng().lat(), lng: marker.getLatLng().lng()});
    marker.closeInfoWindow();
    var new_geometry = gs.createGeometry_(new_geometry_data, true); 
    GEvent.trigger(new_geometry, 'click');
  };

  div.appendChild(html);
  div.appendChild(button);
  return div;
};


geodatastore.adminPanel.prototype.updateHighlightPoly_ = function() {
  var me = this;
  if (me.highlightPoly_) { me.map_.removeOverlay(me.highlightPoly_); }
  if (!me.selected_geometry_) { return; }
  var mapNormalProj = G_NORMAL_MAP.getProjection();
  var mapZoom = me.map_.getZoom();
  if (me.selected_geometry_.data.type == 'point') {
    var latlng = me.selected_geometry_.getLatLng();
    var circle_radius = 20;
  } else {
    //if (me.selected_geometry_.isEditable) return;
    var bounds = me.selected_geometry_.getBounds();
    var latlng = bounds.getCenter();
    var southwest_pixel = mapNormalProj.fromLatLngToPixel(bounds.getSouthWest(), mapZoom);
    var northeast_pixel = mapNormalProj.fromLatLngToPixel(bounds.getNorthEast(), mapZoom);
    var circle_radius = Math.floor(Math.abs(southwest_pixel.x - northeast_pixel.x)*.7);
  }
  var latlngs = [];
  var center_pixel = mapNormalProj.fromLatLngToPixel(latlng, mapZoom);
  for (var a = 0; a<(21); a++) {
    var aRad = 18*a*(Math.PI/180);
    var pixelX = center_pixel.x + circle_radius * Math.cos(aRad);
    var pixelY = center_pixel.y + circle_radius * Math.sin(aRad);
    var polyPixel = new GPoint(pixelX, pixelY);
    var polyPoint = mapNormalProj.fromPixelToLatLng(polyPixel, mapZoom);
    latlngs.push(polyPoint);
  }
  var color = me.selected_geometry_.isEdited ? '#FF0000' : '#FF8921';
  me.highlightPoly_ = new GPolygon(latlngs, '#ff0000', 0, 0.0, color, 0.2, {clickable: false});
  me.map_.addOverlay(me.highlightPoly_);

}
    
geodatastore.adminPanel.prototype.createSidebarEntry_ = function(geometry) {
  var me = this;
  var div = document.createElement('div');
  div.style.cursor = 'pointer';
  div.style.marginBottom = '5px'; 
  if (geometry.isEdited) {
    div.style.backgroundColor = '#F4BFBA';
  } else {
    div.style.backgroundColor = '#fff';
  }

  GEvent.addListener(div, 'highlight', function() {
    for (var i = 0; i < me.dom_.sidebar_divs.length; i++) {
      GEvent.trigger(me.dom_.sidebar_divs[i], 'resetview');
    } 
    me.selected_geometry_ = geometry;
    div.style.backgroundColor = '#FFD7AE';
    me.dom_.sidebar_div.scrollTop = div.offsetTop - me.dom_.sidebar_div.offsetHeight/2;
    me.updateHighlightPoly_();
  });

  GEvent.addDomListener(div, 'click', function() {
    if (me.canUserEdit_(geometry.data.userId)) {
      if (div.className != 'editable_div') {
        GEvent.trigger(div, 'enableedit');
      }
    } else {
      GEvent.trigger(div, 'highlight');
    }
  });

  GEvent.addListener(div, 'dataedit', function() {
    div.style.backgroundColor = '#F4BFBA';
    //me.updateHighlightPoly_();
  });

  GEvent.addListener(div, 'resetview', function() {
    if (!geometry.isEdited) div.style.backgroundColor = '#FFf';
    div.className = 'viewable_div';
    div.innerHTML = '';
    var view_div = me.createView_(geometry, div);
    div.appendChild(view_div);

    if (geometry.data.type == 'point') {
      geometry.disableDragging();
    } else if (geometry.data.type == 'line' || geometry.data.type == 'poly') {
      geometry.disableEditing
      GEvent.clearListeners(geometry,  'mouseover');
      GEvent.clearListeners(geometry,  'mouseout');
    }
  });

  GEvent.addListener(div, 'enableedit', function() {
    for (var i = 0; i < me.dom_.sidebar_divs.length; i++) {
      GEvent.trigger(me.dom_.sidebar_divs[i], 'resetview');
    } 

    if (!geometry.isEdited) { 
      div.style.backgroundColor = '#FFD7AE';
    } else {
      div.style.backgroundColor = '#F4BFBA';
    }
    div.className = 'editable_div';
    div.innerHTML = '';
    var form_div = me.createForm_(geometry, div);
    div.appendChild(form_div);

    me.selected_geometry_ = geometry;
    me.selected_geometry_.isEditable = true;
    if (geometry.data.type == 'point') me.map_.setCenter(geometry.getLatLng());
    else me.map_.setCenter(geometry.getBounds().getCenter());
    
    me.updateHighlightPoly_();
    if (me.selected_geometry_.data.type == 'point') {
      me.selected_geometry_.enableDragging();
    }
    else if (me.selected_geometry_.data.type == 'line' || me.selected_geometry_.data.type == 'poly') {
      GEvent.addListener(geometry, 'mouseover', function() {
        geometry.enableEditing();
      });
      GEvent.addListener(geometry, 'mouseout', function() {
        geometry.disableEditing();
      });
    }
  });

  GEvent.trigger(div, 'resetview');
  me.dom_.sidebar_divs.push(div);
  return div;
}

geodatastore.adminPanel.prototype.createTableRow_ = function(label, value, is_input, geometry) {
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
    value_input.onkeyup = function() {
      geometry.isEdited = true;
      GEvent.trigger(geometry.sidebar_entry, 'dataedit');
    }
    value_td.appendChild(value_input);
  } else {
    value_td.appendChild(document.createTextNode(value));
  }
  tr.appendChild(label_td);
  tr.appendChild(value_td);
  return tr;
}

geodatastore.adminPanel.prototype.createView_ = function(geometry, parent_div) {
  var me = this;
 
  var div = document.createElement('div');
  div.className = 'sidebarview';
  var table = document.createElement('table');
  var tbody = document.createElement('tbody');
  tbody.appendChild(me.createTableRow_('Name', geometry.data.name, false, geometry));
  tbody.appendChild(me.createTableRow_('Description', geometry.data.description, false, geometry));
  tbody.appendChild(me.createTableRow_('Created', geometry.data.userId + ',' + geometry.data.timeStamp, false, geometry));
  table.appendChild(tbody);
  div.appendChild(table);
  if (me.canUserEdit_(geometry.data.userId)) {
    var edit_div = document.createElement('div');
    edit_div.style.textAlign = 'center';
    var edit_button = document.createElement('input');
    edit_button.type = 'button';
    edit_button.value = 'Modify';
    edit_button.onclick = function() {
      GEvent.trigger(parent_div, 'enableedit');
    };
    edit_div.appendChild(edit_button);
    div.appendChild(edit_div);
  }
  return div;
}

geodatastore.adminPanel.prototype.createForm_ = function(geometry, parent_div) {
  var me = this;

  var div = document.createElement('div');
  var table = document.createElement('table');
  var tbody = document.createElement('tbody');
  tbody.appendChild(me.createTableRow_('Name', geometry.data.name, true, geometry));
  tbody.appendChild(me.createTableRow_('Description', geometry.data.description, true, geometry));
  table.appendChild(tbody);
  div.appendChild(table);

  var save_button = document.createElement('input');
  save_button.type = 'button';
  save_button.value = 'Save';
  save_button.onclick = function() {
    me.selected_geometry_.isEditable = false;
    me.selected_geometry_.isEdited = false;
    me.selected_geometry_.hasEnded = true;
    GEvent.trigger(document.getElementById('view_control'),'click');
    parent_div.style.backgroundColor = '#fff';
    me.selected_geometry_.data.name = document.getElementById('name_input').value;
    me.selected_geometry_.data.description = document.getElementById('description_input').value; 
    if (me.selected_geometry_.data.type == 'point') {
      me.selected_geometry_.disableDragging();
      me.selected_geometry_.data.coordinates = [{lat: me.selected_geometry_.getLatLng().lat(), lng:  me.selected_geometry_.getLatLng().lng()}];
    } else if (me.selected_geometry_.data.type == 'line' || me.selected_geometry_.data.type == 'poly') {
      me.selected_geometry_.disableEditing();
      GEvent.clearListeners(me.selected_geometry_,  'mouseover');
      GEvent.clearListeners(me.selected_geometry_,  'mouseout');
      me.selected_geometry_.data.coordinates = [];
      for (var i = 0; i < me.selected_geometry_.getVertexCount(); i++) {
        me.selected_geometry_.data.coordinates.push({lat: me.selected_geometry_.getVertex(i).lat(), lng: me.selected_geometry_.getVertex(i).lng()});
      }
    } 
    if (me.selected_geometry_.data.key) me.saveData_('edit', me.selected_geometry_.data);
    else me.saveData_('add', me.selected_geometry_.data); 
    GEvent.trigger(parent_div, 'resetview');
    me.selected_geometry_ = null;
    me.updateHighlightPoly_();
  }
  div.appendChild(save_button);

  var delete_button = document.createElement('input');
  delete_button.type = 'button'
  delete_button.value = 'Delete';
  delete_button.onclick = function() {
    me.saveData_('delete', me.selected_geometry_.data); 
    // should do this after delete confirmed
    if (me.selected_geometry_.data.type != 'point'){
      me.selected_geometry_.disableEditing;
    }
    me.map_.removeOverlay(me.selected_geometry_);
    me.selected_geometry_ = null;
    me.updateHighlightPoly_();
    me.dom_.sidebar_div.removeChild(parent_div);
  };
  div.appendChild(delete_button);

  var cancel_button = document.createElement('input');
  cancel_button.type = 'button';
  cancel_button.value = 'Cancel';
  cancel_button.onclick = function() {
    GEvent.trigger(parent_div, 'resetview');
    me.selected_geometry_ = null;
    me.updateHighlightPoly_();
  };
  div.appendChild(cancel_button); 
  return div;
};

geodatastore.adminPanel.prototype.loadKmlData_ = function() {
  var me = this;
  var url_base = 'gen/';
  var url = url_base + 'request?operation=get&output=json'
  //&userid=' + current_user;
  GDownloadUrl(url, function(data, responseCode) { me.handleDataResponse_(me, data, responseCode); });
};

geodatastore.adminPanel.prototype.saveData_ = function(type, data) {
  var url  = 'gen/request?';
  var url_params = ['operation=' + type];
  for (var data_key in data) {
    var subdata = data[data_key];
    if (subdata instanceof Array) {
      for (var i = 0; i < subdata.length; i++) {
        for (var subdata_key in subdata[i]) {
          url_params.push(subdata_key + '=' + subdata[i][subdata_key]);
        }
      }
    } else {
      url_params.push(data_key + '=' + data[data_key])
    }
  }
  //url += url_params.join('&');
  //GDownloadUrl(url, this.handleDataResponse_, url_params.join('&'));
  url += url_params.join('&');
  GDownloadUrl(url, this.handleDataResponse_);
};

geodatastore.adminPanel.prototype.handleDataResponse_ = function(me, data, responseCode) {
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


geodatastore.adminPanel.prototype.createGeometry_ = function(data, is_editable) {
  var me = this;
  data.name = unescape(data.name);
  data.description = unescape(data.description);

  if (data.type == 'point') {
    var geometry = new GMarker(new GLatLng(data.coordinates[0].lat, data.coordinates[0].lng), {draggable: true, icon: me.icons_.unchanged});
  } else if (data.type == 'line' || data.type == 'poly') {
    var latlngs = [];
    for (var i = 0; i < data.coordinates.length; i++) {
      latlngs.push(new GLatLng(data.coordinates[i].lat, data.coordinates[i].lng));
    }
    var geometry = (data.type == 'line') ? new GPolyline(latlngs) : new GPolygon(latlngs, '#0000ff', 2, 0.7, '#0000ff', 0.2);
  }
  geometry.data = data;
  if (me.canUserEdit_(geometry.data.userId)) {
    geometry.isEdited = is_editable;
    geometry.isEditable = is_editable;
    geometry.hasEnded = !is_editable;
  }

  var sidebar_entry = me.createSidebarEntry_(geometry);
  if (me.dom_.sidebar_divs.length > 1) {
    //me.dom_.sidebar_div.insertBefore(sidebar_entry);
    var last_sidebar_entry = me.dom_.sidebar_divs[me.dom_.sidebar_divs.length-2];
    me.dom_.sidebar_div.insertBefore(sidebar_entry, last_sidebar_entry);
  } else {
    me.dom_.sidebar_div.appendChild(sidebar_entry);
  }
  geometry.sidebar_entry = sidebar_entry;
  if (is_editable) {
    GEvent.trigger(geometry.sidebar_entry, 'enableedit');
  }
  this.map_.addOverlay(geometry);
  this.geometries_.push(geometry);

  GEvent.addListener(geometry, 'click', function() {
    GEvent.trigger(geometry.sidebar_entry, 'highlight');
  });

  if (me.canUserEdit_(geometry.data.userId)) { 
    GEvent.addListener(geometry, 'click', function() {
      GEvent.trigger(geometry.sidebar_entry, 'enableedit');
    });

    if (geometry.data.type == 'point') {
      GEvent.addListener(geometry, 'dragend', function() {
        geometry.isEdited = true;
        me.updateHighlightPoly_();
        GEvent.trigger(geometry.sidebar_entry, 'dataedit');
      });
    } else if (geometry.data.type == 'line' || geometry.data.type == 'poly') {
      GEvent.addListener(geometry, 'endline', function() {
        geometry.isEdited = true;
        geometry.hasEnded = true;
        GEvent.trigger(geometry.sidebar_entry, 'dataedit');
      });
      GEvent.addListener(geometry, 'lineupdated', function() {
        geometry.isEdited = true;
        me.updateHighlightPoly_();
        GEvent.trigger(geometry.sidebar_entry, 'dataedit');
      });
      if (is_editable) {
        me.selected_geometry_ = geometry;
        geometry.enableDrawing();
      }
    }
  }
  return geometry;
}
 
function EditControl() {
}

EditControl.prototype = new GControl();

EditControl.prototype.initialize = function(map) {
  var me = this;
  me.buttons_ = [];
 
  var control_div = document.createElement('div'); 
  var control_table = document.createElement('table');
  var control_tr = document.createElement('tr');
  
  var vc_opts = {img_url: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bsu.png',
                 img_hover_url: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bsd.png',
                 name: 'view', tooltip: 'Select geometries by clicking on them.'};
  var view_button = this.createButton_(vc_opts);
  var view_td = document.createElement('td');
  view_td.appendChild(view_button.img);

  var mc_opts = {img_url: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bmu.png',
                 img_hover_url: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bmd.png',
                 name: 'point', tooltip: 'Click on the map to create a new marker.'};
  var marker_button = this.createButton_(mc_opts);
  var marker_td = document.createElement('td');
  marker_td.appendChild(marker_button.img);

  var lc_opts = {img_url: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Blu.png',
                 img_hover_url: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bld.png',
                 name: 'line', tooltip: 'Click on the map to start creating a new line.'};
  var line_button = this.createButton_(lc_opts);
  var line_td = document.createElement('td');
  line_td.appendChild(line_button.img);

  var pc_opts = {img_url: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bpu.png',
                 img_hover_url: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bpd.png',
                 name: 'poly', tooltip: 'Click on the map to start creating a new filled poly.'};
  var poly_button = this.createButton_(pc_opts);
  var poly_td = document.createElement('td');
  poly_td.appendChild(poly_button.img);

  control_tr.appendChild(view_td);
  control_tr.appendChild(marker_td);
  control_tr.appendChild(line_td);
  control_tr.appendChild(poly_td);
  control_table.appendChild(control_tr);
  control_div.appendChild(control_table);
  GEvent.trigger(view_button.img, 'click');
  map.getContainer().appendChild(control_div);
  return control_div;
} 
 
EditControl.prototype.createButton_ = function(button_opts) {
  var me = this;
  var button = {};
  button.opts = button_opts;

  var button_img = document.createElement('img');
  button_img.style.cursor = 'pointer';
  button_img.width = '33';
  button_img.height = '33';
  button_img.border = '0';
  button_img.src = button_opts.img_url;
  button_img.id = button_opts.name+'_control';
  GEvent.addDomListener(button_img, "click", function() { 
    for (var i = 0; i < me.buttons_.length; i++) {
      me.buttons_[i].img.src = me.buttons_[i].opts.img_url;
    }
    button_img.src = button_opts.img_hover_url;  
    GEvent.trigger(me, button_opts.name);
  });  

  button.img = button_img;
  me.buttons_.push(button);
  return button;
}

EditControl.prototype.getDefaultPosition = function() {
  return new GControlPosition(G_ANCHOR_BOTTOM_LEFT, new GSize(260, 0));
}

function StatusControl() {
}

StatusControl.prototype = new GControl();

StatusControl.prototype.initialize = function(map) {
  var me = this;
  var status_div = document.createElement('span');
  status_div.style.color = 'grey';
  status_div.style.backgroundColor = 'white';
  status_div.style.border = '1px solid grey';
  status_div.style.padding = '5px';
  status_div.innerHTML = 'Select geometries by clicking on them.';
  this.status_div = status_div;
  map.getContainer().appendChild(status_div);
  return this.status_div;
}

StatusControl.prototype.setText = function(text) {
  this.status_div.innerHTML = text;
}

StatusControl.prototype.getDefaultPosition = function() {
  return new GControlPosition(G_ANCHOR_BOTTOM_LEFT, new GSize(420, 5));
}
 
