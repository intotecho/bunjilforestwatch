import React from 'react';
import { categories, categoryImages } from '../constants';
import {
  GoogleMapLoader, GoogleMap, Marker,
  Polyline, Polygon, InfoWindow
} from "react-google-maps";

export default React.createClass({
  getInitialState() {
    return {
      renderClusters: true
    }
  },

  componentWillReceiveProps(nextProps) {
    if (this.props.clusterId != nextProps.clusterId) {
      this.setState({
        renderClusters: true
      });
    }
  },

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

  renderClusterAlerts() {
    if (!this.state.renderClusters) { return; }

    const { properties, id } = this.props.features[0];
    const coordinates = properties.points.coordinates;

    setTimeout(() => this.setState({ renderClusters: false }), 3000);

    return coordinates.map((alertCoordinates, index) => {
      const googleCoordinates = new google.maps.LatLng(alertCoordinates[1], alertCoordinates[0]);

      return (
        <Marker
          key={`json-${id}-${index}`}
          position={googleCoordinates}
          icon={require('../../images/geo_cluster.png')}
          {...properties}>
        </Marker>
      );
    });
  },

  getMapCoordinates() {
    // You must parseFloat since Google Maps expects a real number
    // Lat and Long are both strings due to JSX interpolation {}
    return {
      lat: parseFloat(this.props.lat),
      lng: parseFloat(this.props.long)
    };
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
              {this.renderClusterAlerts()}
            </GoogleMap>
          }
        />
      </section>
    );
  }
});
