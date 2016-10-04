import React from 'react';
import Request from 'superagent';
import {
  GoogleMapLoader, GoogleMap, Marker,
  Polyline, Polygon, InfoWindow
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

  regenerateOverlay(clusterId) {
    Request
    .get('overlay/regenerate/' + clusterId)
    .end();
  },

  // FIXME: Hack
  renderMapOverlay(googleMapComponent) {
    // Prop retrieval hack, component may not exist by then
    if (!googleMapComponent) { return; }

    let { overlays, clusterId } = this.props;
    const { map } = googleMapComponent.props;

    // If actual google map's object doesn't exist
    if (!map) { return ; }

    overlays.forEach((overlay) => {
      this.hasExpired(overlay);
      map.overlayMapTypes.push(this.getGoogleOverlay(overlay));
    });
  },

  hasExpired(overlay) {
    const self = this;
    let testURL = ['https://earthengine.googleapis.com/map', overlay.map_id, 1, 0, 0].join("/");

    testURL += '?token=' + overlay.token;

    Request
    .get(testURL)
    .end(function (err, res) {
      if (err || !res.ok) {
        if (self.props.clusterId) {
          self.regenerateOverlay(self.props.clusterId);
        }
        return true;
      }
    });

    return false;
  },

  getGoogleOverlay(overlay) {
    var eeMapOptions = {
      getTileUrl: (tile, zoom) => {
        var url = [
          'https://earthengine.googleapis.com/map',
          overlay.map_id, zoom, tile.x, tile.y
        ].join("/");

        url += '?token=' + overlay.token;

        /*
          Source: overlay-mgr.js, LN:274 (as of 4th Oct 2016)

          Code is missing pending URL checks, please check if
          this is important
        */

        return url;
      },
      tileSize: new google.maps.Size(256, 256)
    };

    return new google.maps.ImageMapType(eeMapOptions);
  },

  render() {
    return (
      <section style={{ height: "95%" }}>
        <GoogleMapLoader
          containerElement={ <div style={{ height: "100%", width: "100%" }} /> }
          googleMapElement={
            <GoogleMap
              ref={(googleMapComponent) => this.renderMapOverlay(googleMapComponent)}
              mapTypeId='satellite'
              defaultZoom={16}
              center={this.getMapCoordinates()}
              options={{
                streetViewControl: false,
                mapTypeControl: false
              }}>
              {this.renderObsTaskBoundary()}
              {this.renderMapOverlay()}
            </GoogleMap>
          }
        />
      </section>
    );
  }
});
