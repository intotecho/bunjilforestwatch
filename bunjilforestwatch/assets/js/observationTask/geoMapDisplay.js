import React from 'react';
import Request from 'superagent';
import {
  GoogleMapLoader, GoogleMap, Marker,
  Polyline, Polygon, InfoWindow, OverlayView
} from "react-google-maps";

export default React.createClass({
  geometryToComponentWithLatLng(geometry) {
    let type;
    const isArray = Array.isArray(geometry);
    let coordinates = isArray ? geometry : geometry.coordinates;

    if (geometry.type === 'Polygon') {
      type = geometry.type;
    } else if (isArray && geometry.length > 2) {
      type = 'LineString';
    } else {
      type = 'Point';
    }

    switch (type) {
      case `Polygon`:
        return {
          ElementClass: Polygon,
          paths: coordinates.map(this.geometryToComponentWithLatLng, { type: `LineString` })[0],
          options: { strokeColor: '#6495ed', fillColor: '#6495ed' }
        };
      case `LineString`:
        coordinates = coordinates.map(this.geometryToComponentWithLatLng, { type: `Point` });
        return isArray ? coordinates : {
          ElementClass: Polyline,
          path: coordinates
        };
      case `Point`:
        coordinates = new google.maps.LatLng(coordinates[1], coordinates[0]);
        return isArray ? coordinates : {
          ElementClass: Marker,
          ChildElementClass: InfoWindow,
          position: coordinates
        };
      default:
        throw new TypeError(`Unknown geometry type: ${ type }`);
    }
  },

  renderObsTaskBoundary() {
    /*
      WARNING: This function may break in the future, or not work as intended
      Source example: http://react-google-maps.tomchentw.com/#/geojson?_k=5myn14
    */
    return this.props.features.reduce((array, feature, index) => {
      const { properties } = feature;
      const { ElementClass, ChildElementClass, ...geometry } = this.geometryToComponentWithLatLng(feature.geometry);

      array.push(
        <ElementClass
          key={`json-${feature.id}`}
          {...properties}
          {...geometry}>
        </ElementClass>
      );

      return array;
    }, [], this);
  },

  getMapCoordinates() {
    const { lat = 0.0, long = 0.0 } = this.props;

    // You must parseFloat since Google Maps expects a real number
    // Lat and Long are both strings due to JSX interpolation {}
    return {
      lat: parseFloat(lat),
      lng: parseFloat(long)
    };
  },

  // Remove when endpoints are ready and fix renderMapOverlay()
  testRenderMapOverlay() {
    const { lat = 0.0, long = 0.0 } = this.props;
    // Pretend we made a request to get an image
    const cogwheelSrc = require('../../images/cogwheel.png');

    // Pretend new Array is overlay data set from props
    let overlays = [1,2,3,4,5,6,7,8,9,10];

    return overlays.map((value) => {
      const lLat = parseFloat(lat) + (Math.random() * 0.5);
      const lLong = parseFloat(long) + (Math.random() * 0.5);

      return (
        <OverlayView
          key={value}
          position={{ lat: lLat, long: lLong }}
          mapPaneName={OverlayView.OVERLAY_LAYER}>
          <img src={cogwheelSrc} />
        </OverlayView>
      );
    });
  },

  renderMapOverlay() {
    // TODO: Hook ObservationTask to pass both data down
    // let { overlays, gladClusterId } = this.props;

    // if (!overlays) {
    //   overlays = this.createOverlay(gladClusterId);
    // }

    // overlays.forEach((overlay) => {
    //   const = eeMapAPIUrl = 'https://earthengine.googleapis.com/map';
    //   let overlayTileUrl = [eeMapAPIUrl, overlay.map_id, 1, 0, 0].join("/");

    //   overlayTileUrl += '?token=' + overlay.token;

    //   Request
    //   .get(overlayTileUrl)
    //   .end(
    //     function (err, res) {
    //       if (err || !res.ok) {
    //         overlay = this.regenerateOverlay(overlay.map_id);
    //       }
    //     }
    //   );
    // });

    // displayOverlay(overlay);
  },

  createOverlay(gladClusterId) {
    Request
    .get('overlay/create/' + gladClusterId)
    .end(
      function (err, res) {
        if (err === null && res.ok) {
          return JSON.parse(res.text);
        }
      }
    );
  },

  regenerateOverlay(gladClusterId) {
    Request
    .get('overlay/regenerate/' + gladClusterId)
    .end(
      function (err, res) {
        if (err === null && res.ok) {
          return JSON.parse(res.text);
        }
      }
    );
  },

  render() {
    return (
      <section style={{ height: "95%" }}>
        <GoogleMapLoader
          containerElement={ <div style={{ height: "100%", width: "100%" }} /> }
          googleMapElement={
            <GoogleMap
              mapTypeId='satellite'
              defaultZoom={16}
              center={this.getMapCoordinates()}
              options={{
                streetViewControl: false,
                mapTypeControl: false
              }}>
              {this.renderObsTaskBoundary()}
              {this.testRenderMapOverlay()}
            </GoogleMap>
          }
        />
      </section>
    );
  }
});
