import React from 'react';

import { GoogleMapLoader, GoogleMap, Marker,
         Polyline, Polygon, InfoWindow } from "react-google-maps";

export default React.createClass({
  geometryToComponentWithLatLng(geometry) {
    let type;
    const isArray = Array.isArray(geometry);

    // Manually determine the type
    if (geometry.type === 'Polygon') {
      type = geometry.type;
    } else if (isArray && geometry.length > 2) {
      type = 'LineString';
    } else {
      type = 'Point';
    }

    let coordinates = isArray ? geometry : geometry.coordinates;

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

  renderGeometry() {
    /*
      WARNING: This function may break in the future, or not work as intended
      Source example: http://react-google-maps.tomchentw.com/#/geojson?_k=5myn14

      - As of current, spreading geometry returns no attributes
      - Child element is not included
      - Element states is not included
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

  renderClusterAlerts() {
    const { properties, id } = this.props.features[0];
    const coordinates = properties.points.coordinates;

    return coordinates.map((alertCoordinates) => {
      const googleCoordinates = new google.maps.LatLng(alertCoordinates[1], alertCoordinates[0]);

      return (
        // TODO: Render markers as a custom image icon
        <Marker
          key={`json-${id}-${Math.random() * Date.now()}`}
          position={googleCoordinates}
          {...properties}>
        </Marker>
      );
    });
  },

  render() {

    // You must parseFloat since Google Maps expects a real number
    // Lat and Long are both strings due to JSX interpolation {}
    const coords = {
      lat: parseFloat(this.props.lat),
      lng: parseFloat(this.props.long)
    };

    return (
      <section style={{ height: "95%" }}>
        <GoogleMapLoader
          containerElement={ <div style={{ height: "100%", width: "100%" }} /> }
          googleMapElement={
            <GoogleMap
              mapTypeId='satellite'
              defaultZoom={16}
              center={coords}
              options={{
                streetViewControl: false,
                mapTypeControl: false
              }}>
              {this.renderGeometry()}
              {this.renderClusterAlerts()}
            </GoogleMap>
          }
        />
      </section>
    );
  }
});
