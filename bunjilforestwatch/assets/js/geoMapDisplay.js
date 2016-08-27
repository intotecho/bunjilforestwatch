import React from 'react';

import styles from '../stylesheets/geoMapDisplay';
import { GoogleMapLoader, GoogleMap, Marker } from "react-google-maps";

export default React.createClass({
  render() {
    return (
	    <section style={styles.GeoMapDisplayContainer}>
	      <GoogleMapLoader
	        containerElement={
	          <div style={styles.GeoMapDisplayMapContainer} />
	        }
	        googleMapElement={
	          <GoogleMap
	            ref={(map) => console.log(map)}
	            mapTypeId='satellite'
	            defaultZoom={12}
	            defaultCenter={{ lat: -25.363882, lng: 131.044922 }}>
	          </GoogleMap>
	        }
	      />
	    </section>
    );
  }
});
