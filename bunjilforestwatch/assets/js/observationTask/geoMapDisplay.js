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
        };
      case `LineString`:
        coordinates = coordinates.map(this.geometryToComponentWithLatLng, { type: `Point` });
        return isArray ? coordinates : {
          ElementClass: Polyline,
          path: coordinates,
        };
      case `Point`:
        coordinates = new google.maps.LatLng(coordinates[1], coordinates[0]);
        return isArray ? coordinates : {
          ElementClass: Marker,
          ChildElementClass: InfoWindow,
          position: coordinates,
        };
      default:
        throw new TypeError(`Unknown geometry type: ${ type }`);
    }
  },

  render() {
    /*
      WARNING: This function may break in the future, or not work as intended
      Source example: http://react-google-maps.tomchentw.com/#/geojson?_k=5myn14

      - As of current, spreading geometry returns no attributes
      - Child element is not included
      - Element states is not included
      - Certain attributes do not work (e.g. fillColor, strokeColor, etc)
    */
    const mapElements = this.props.features.reduce((array, feature, index) => {
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

    // You must parseFloat since Google Maps expects a real number
    // Lat and Long are both strings due to JSX interpolation {}
    const coords = {
      lat: parseFloat(this.props.lat),
      lng: parseFloat(this.props.long)
    };

    return (
      <section style={{ height: "100%" }}>
        <GoogleMapLoader
          containerElement={ <div style={{ height: "100%", width: "100%" }} /> }
          googleMapElement={
            <GoogleMap
              mapTypeId='satellite'
              defaultZoom={16}
              defaultCenter={coords}>
              {mapElements}
            </GoogleMap>
          }
        />
      </section>
    );
  }
});
