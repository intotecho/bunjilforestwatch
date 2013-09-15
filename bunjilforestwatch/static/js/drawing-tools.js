/*******************************************************************************
Copyright (c) 2013
Licences: Creative Commons Attribution 
******************************************************************************/

function createDrawingManager(map) {
	var drawingManager = new google.maps.drawing.DrawingManager({
	    drawingMode: google.maps.drawing.OverlayType.MARKER,
	    drawingControl: true,
	    drawingControlOptions: {
	      position: google.maps.ControlPosition.TOP_CENTER,
	      drawingModes: [
	        google.maps.drawing.OverlayType.MARKER,
	        google.maps.drawing.OverlayType.CIRCLE,
	        google.maps.drawing.OverlayType.POLYGON,
	        google.maps.drawing.OverlayType.POLYLINE,
	        google.maps.drawing.OverlayType.RECTANGLE
	      ]
	    },
	    markerOptions: {
	      icon: '/static/img/road-icon.png'
	    },
	    circleOptions: {
	      fillColor: '#ffff00',
	      fillOpacity: 0.5,
	      strokeWeight: 2,
	      clickable: false,
	      editable: true,
	      zIndex: 1
	    }
	  });
	  drawingManager.setMap(map);
};