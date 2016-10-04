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

  regenerateOverlay(overlayKey) {
    return new Promise((resolve) => {
      Request
      .get('overlay/regenerate/' + overlayKey)
      .end((err, res) => {
        if (!err && res.ok) {
          resolve(JSON.parse(res.text));
        } else {
          resolve();
        }
      });
    });
  },

  renderMapOverlays(googleMapComponent) {
    // FIXME: Hacked prop retrieval hack, component may not exist by then
    if (!googleMapComponent) { return; }

    const { hasExpired, regenerateOverlay, getGoogleOverlay } = this;
    const { overlays } = this.props;
    const { map } = googleMapComponent.props;

    // If actual google map's object doesn't exist
    if (!map) { return; }

    overlays.forEach((overlay) => {
      hasExpired(overlay).then((hasExpired) => {
        // If image has expired, then regenerate it, else push data
        if (hasExpired) {
          regenerateOverlay(overlay.key).then((newOverlay) => {
            if (newOverlay) {
              // Push using new overlay data obtained from request
              map.overlayMapTypes.push(getGoogleOverlay(newOverlay));
            }
          });
        } else {
          map.overlayMapTypes.push(getGoogleOverlay(overlay));
        }
      });
    });
  },

  hasExpired(overlay) {
    return new Promise((resolve) => {
      resolve(() => {
        let testURL = ['https://earthengine.googleapis.com/map', overlay.map_id, 1, 0, 0].join("/");

        testURL += '?token=' + overlay.token;

        Request
        .get(testURL)
        .end(function (err, res) {
          if (err || !res.ok) {
            if (overlay.key) {
              self.regenerateOverlay(overlay.key);
            }
            return true;
          }
        });

        return false;
      });
    });
  },

  getGoogleOverlay(overlay) {
    var eeMapOptions = {
      getTileUrl: (tile, zoom) => {
        var url = [
          'https://earthengine.googleapis.com/map',
          overlay.map_id, zoom, tile.x, tile.y
        ].join("/");

        url += '?token=' + overlay.token;

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
              ref={(googleMapComponent) => this.renderMapOverlays(googleMapComponent)}
              mapTypeId='satellite'
              defaultZoom={16}
              center={this.getMapCoordinates()}
              options={{
                streetViewControl: false,
                mapTypeControl: false
              }}>
              {this.renderObsTaskBoundary()}
            </GoogleMap>
          }
        />
      </section>
    );
  }
});
