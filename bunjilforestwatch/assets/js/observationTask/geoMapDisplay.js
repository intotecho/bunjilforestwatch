import React from 'react';

import { GoogleMapLoader, GoogleMap, Marker } from "react-google-maps";
// import styles from '../stylesheets/geoMapDisplay'; //FIXME: component styling issues

export default React.createClass({
  render() {
  	// You must parseFloat since Google Maps expects a real number
  	// Lat and Long are both strings due to JSX interpolation {}
  	let coords = {
  		lat: parseFloat(this.props.lat),
  		lng: parseFloat(this.props.long)
  	};

    return (
	    <section style={{height: "100%"}}>
	      <GoogleMapLoader
	        containerElement={
	          <div style={{ height: "80%", width: "50%" }} />
	        }
	        googleMapElement={
	          <GoogleMap
	            mapTypeId='satellite'
	            defaultZoom={12}
	            defaultCenter={coords}>
	          </GoogleMap>
	        }
	      />
	    </section>
    );
  }
});
