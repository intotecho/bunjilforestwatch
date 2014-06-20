/*******************************************************************************
Copyright (c) 2010-2012. Gavin Harriss, Modified by Chris Goodman 2013 for Bunjil.
Site: http://www.gavinharriss.com/
Originally developed for: http://www.topomap.co.nz/
Licences: Creative Commons Attribution 3.0 New Zealand License
http://creativecommons.org/licenses/by/3.0/nz/
******************************************************************************/
var OPACITY_MAX_PIXELS = 57; // Width of opacity control image
var initialOpacity = 100;

function createOpacityControl(map, opacity, layerLabel) {
	var sliderImageUrl = "/static/img/opacity-slider3d7.png";
	
	// Create main div to hold the control.
	var mainDiv = document.createElement('DIV');	
	mainDiv.setAttribute("style", "topmargin=0;margin:5px;width:71px;height:42px;");

	var opacityDiv = document.createElement('DIV');
	opacityDiv.setAttribute("style", "topmargin=0;margin:0px;overflow-x:hidden;overflow-y:hidden;background:url(" + sliderImageUrl + ") no-repeat;width:71px;height:21px;cursor:pointer;");

	////Create Label (CG Mods) 
	var opacityLabelDiv = document.createElement('DIV');
	opacityLabelDiv.setAttribute("style", "text-align:center;position:relative;center:0px;top:0px;opacity:0.6;background-color:#cccccc;width:71px;height:21px;");
	opacityLabelDiv.setAttribute('onselectstart', "return false");
	opacityLabelDiv.appendChild(document.createTextNode(layerLabel));
	
	
	// Create knob
	var opacityKnobDiv = document.createElement('DIV');
	opacityKnobDiv.setAttribute("style", "padding:0;margin:0;overflow-x:hidden;overflow-y:hidden;background:url(" + sliderImageUrl + ") no-repeat -71px 0;width:14px;height:21px;");
	opacityDiv.appendChild(opacityKnobDiv);

	var opacityCtrlKnob = new ExtDraggableObject(opacityKnobDiv, {
		restrictY: true,
		container: opacityDiv
	});

	mainDiv.appendChild(opacityDiv);
	mainDiv.appendChild(opacityLabelDiv);

	google.maps.event.addListener(opacityCtrlKnob, "dragend", function () {
		setOpacity(opacityCtrlKnob.valueX());
	});
 
	google.maps.event.addDomListener(opacityDiv, "click", function (e) {
		var left = findPosLeft(this);
		var x = e.pageX - left - 5; // - 5 as we're using a margin of 5px on the div
		opacityCtrlKnob.setValueX(x);
		setOpacity(x);
	});

	map.controls[google.maps.ControlPosition.RIGHT_TOP].push(mainDiv);
	//map.controls[google.maps.ControlPosition.TOP_RIGHT].push(opacityLabelDiv);

	// Set initial value
	var initialValue = OPACITY_MAX_PIXELS / (100 / opacity);
	opacityCtrlKnob.setValueX(initialValue);
	setOpacity(initialValue);
}

function setOpacity(pixelX, overlay) {
	// Range = 0 to OPACITY_MAX_PIXELS
	var value = (100 / OPACITY_MAX_PIXELS) * pixelX;
	if (value < 0) value = 0;
	if (value == 0) {
		if (overlay.visible == true) {
			overlay.hide();
		}
	}
	else {
		overlay.setOpacity(value);
		if (overlay.visible == false) {
			overlay.show();
		}
	}
	overlay.redraw()
}

function findPosLeft(obj) { //for slider
	var curleft = 0;
	if (obj.offsetParent) {
		do {
			curleft += obj.offsetLeft;
		} while (obj = obj.offsetParent);
		return curleft;
	}
	return undefined;
}

CustomTileOverlay = function (map, opacity, mapid, token) {
	this.tileSize = new google.maps.Size(256, 256); // Change to tile size being used
	
	this.minZoom = 1;
	this.maxZoom = 100;
	
	this.map = map;
	this.opacity = opacity;
	this.tiles = [];
	
	this.visible = false;
	this.initialized = false;
	
	this.self = this;
	this.mapid = mapid;
	this.token = token;
}

CustomTileOverlay.prototype = new google.maps.OverlayView();

CustomTileOverlay.prototype.getTile = function (p, z, ownerDocument) {
	// If tile already exists then use it
	for (var n = 0; n < this.tiles.length; n++) {
		if (this.tiles[n].id == 't_' + p.x + '_' + p.y + '_' + z) {
			//console.log("getTile: already got: ", this.tiles[n].id , n, this.tiles[n].style.backgroundImage);
			return this.tiles[n];
		}
	}

	// If tile doesn't exist then create it
	var tile = ownerDocument.createElement('div');
	var tp = this.getTileUrlCoord(p, z);
	tile.id = 't_' + tp.x + '_' + tp.y + '_' + z
	tile.style.width = this.tileSize.width + 'px';
	tile.style.height = this.tileSize.height + 'px';
	tile.style.backgroundImage = 'url(' + this.getTileUrl(tp, z) + ')';
	tile.style.backgroundRepeat = 'no-repeat';
	
	tile.style.border = "0px"; // hide border
	
	if (!this.visible) {
		tile.style.display = 'none';
	}

	this.tiles.push(tile)

	this.setObjectOpacity(tile);
	//console.log("getTile: fetch new: ", tile.id, tile.style.backgroundImage);

	return tile;
}

CustomTileOverlay.prototype.deleteHiddenTiles = function (zoom) {
	// Save memory / speed up the display by deleting tiles out of view
	// Essential for use on iOS devices such as iPhone and iPod!
	
	var bounds = this.map.getBounds();
	var tileNE = this.getTileUrlCoordFromLatLng(bounds.getNorthEast(), zoom);
	var tileSW = this.getTileUrlCoordFromLatLng(bounds.getSouthWest(), zoom);

	var minX = tileSW.x - 1;
	var maxX = tileNE.x + 1;
	var minY = tileSW.y - 1;
	var maxY = tileNE.y + 1;

	var tilesToKeep = [];
	var tilesLength = this.tiles.length;
	for (var i = 0; i < tilesLength; i++) {
		var idParts = this.tiles[i].id.split("_");
		var tileX = Number(idParts[1]);
		var tileY = Number(idParts[2]);
		var tileZ = Number(idParts[3]);
		if ((
				(minX < maxX && (tileX >= minX && tileX <= maxX))
				|| (minX > maxX && ((tileX >= minX && tileX <= (Math.pow(2, zoom) - 1)) || (tileX >= 0 && tileX <= maxX))) // Lapped the earth!
			)
			&& (tileY >= minY && tileY <= maxY)
			&& tileZ == zoom) {
			tilesToKeep.push(this.tiles[i]);
		}
		else {
			delete this.tiles[i];
		}
	}
	
	this.tiles = tilesToKeep;
};

CustomTileOverlay.prototype.pointToTile = function (point, z) {
	var projection = this.map.getProjection();
	//console.log("projection: ", projection);
	var worldCoordinate = projection.fromLatLngToPoint(point);
	var pixelCoordinate = new google.maps.Point(worldCoordinate.x * Math.pow(2, z), worldCoordinate.y * Math.pow(2, z));
	var tileCoordinate = new google.maps.Point(Math.floor(pixelCoordinate.x / this.tileSize.width), Math.floor(pixelCoordinate.y / this.tileSize.height));
	return tileCoordinate;
}

CustomTileOverlay.prototype.getTileUrlCoordFromLatLng = function (latlng, zoom) {
	return this.getTileUrlCoord(this.pointToTile(latlng, zoom), zoom)
}

CustomTileOverlay.prototype.getTileUrlCoord = function (coord, zoom) {
	//  Alternate expression	
	//	max = Math.pow(2, zoom),
	//  coordX = coord.x < 0 ? max + coord.x : coord.x,
	//  coordY = coord.y < 0 ? max + coord.y : coord.y,
	//  if (coordX > max) { coordX = coordX - max }
	//  if (coordY > max) { coordY = coordY - max }
	var tileRange = 1 << zoom;
	var y = coord.y; 	//var y = tileRange - coord.y - 1; Original code had this inverted.
	var x = coord.x;
	if (x < 0 || x >= tileRange) {
		x = (x % tileRange + tileRange) % tileRange;
	}
	if (y < 0 || y >= tileRange) {
		y = (y % tileRange + tileRange) % tileRange;
	}
	return new google.maps.Point(x, y);

}

CustomTileOverlay.prototype.getTileUrl = function (coord, zoom) {
	//Modified to support Earth Engine tiles.
	//from mapclient.py:  return '%s/map/%s/%d/%d/%d?token=%s' % (_tile_base_url, mapid['mapid'], z, x, y, mapid['token'])
	// https://earthengine.googleapis.com//map/0d5c4ebb14ddafdb264ca2bb76fd41c4/11/171/-42?token=4111ca3429e7173813dfeab801764e85
	//src="https://maps.googleapis.com/maps/api/js/StaticMapService.GetMapImage?1m2&1i212628&2i132212&2e2&3u9&4m3&1u2544&2u594&3e2&5m4&1e3&5sen-US&6sus&10b0&token=33834"
	
	BASE_URL = 'https://earthengine.googleapis.com';

	if(this.mapid)
	{
		url = (BASE_URL + '/map/' + this.mapid + '/' + zoom + '/' + coord.x + '/' + coord.y +  '?token=' + this.token);
		//console.log(url);
		return url;
	}
	else {
		console.log('No mapid, blank tile returned.');
		return "/static/img/blanktile.png";
	}
}

CustomTileOverlay.prototype.initialize = function () {
	if (this.initialized) {
		return;
	}
	var self = this.self;
	this.map.overlayMapTypes.insertAt(0, self);
	this.initialized = true;
	this.map_id = null;
}

CustomTileOverlay.prototype.hide = function () {
	this.visible = false;

	var tileCount = this.tiles.length;
	for (var n = 0; n < tileCount; n++) {
		this.tiles[n].style.display = 'none';
	}
}

CustomTileOverlay.prototype.show = function () {
	this.initialize();
	this.visible = true;
	var tileCount = this.tiles.length;
	for (var n = 0; n < tileCount; n++) {
		this.tiles[n].style.display = '';
	}
}

CustomTileOverlay.prototype.releaseTile = function (tile) {
	tile = null;
}

CustomTileOverlay.prototype.setOpacity = function (op) {
	this.opacity = op;

	var tileCount = this.tiles.length;
	for (var n = 0; n < tileCount; n++) {
		this.setObjectOpacity(this.tiles[n]);
	}
}

CustomTileOverlay.prototype.setObjectOpacity = function (obj) {
	console.log("object style: %s, %s, %s, %s.", obj.style.filter, obj.style.KHTMLOpacity, obj.style.MozOpacity, obj.style.opacity );
	if (this.opacity > 0) {
		if (typeof (obj.style.filter) == 'string') { obj.style.filter = 'alpha(opacity:' + this.opacity + ')'; }
		if (typeof (obj.style.KHTMLOpacity) == 'string') { obj.style.KHTMLOpacity = this.opacity / 100; }
		if (typeof (obj.style.MozOpacity) == 'string') { obj.style.MozOpacity = this.opacity / 100; }
		if (typeof (obj.style.opacity) == 'string') { obj.style.opacity = this.opacity / 100; }
	}
}
