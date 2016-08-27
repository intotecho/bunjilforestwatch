import { render } from 'react-dom';
import React from 'react';

import LinkButton from './linkButton';
import GeoMapDisplay from './geoMapDisplay';
import Request from 'superagent';

import { hello } from '../stylesheets/indexUser2';
import { uSizeFull } from '../stylesheets/utils';

var IndexUser2 = React.createClass({
  getInitialState() {
    return {
      isTaskReady: false,
      areaId: -1,
      case: {},
      gladCluster: {}
    };
  },

  render() {
    let geoMapDisplay;

    if (this.state.isTaskReady === true) {
      // Ugly ultra hacky data retrieval
      let coords = this.state.gladCluster.geojson.features[0].properties.points.coordinates[0];
      let long = coords[0];
      let lat = coords[1];

      geoMapDisplay = <GeoMapDisplay long={long} lat={lat} />;
    } else {
      // Small hack, not sure how to function bind on Superagent
      let self = this;

      // Fire off get request before component starts rendering
      Request
      .get('/observation-task/next')
      .end(
        function(err, res) {
          if (err === null && res.statusCode === 200) {
            // Response is coming back as JSON string
            let response = JSON.parse(res.text);
            console.log(response);

            self.setState({
              isTaskReady: true,
              areaId: response.area_id,
              case: response.case,
              gladCluster: response.glad_cluster
            });
          }
        }
      );
    }

    return (
      <div>
        <LinkButton name='Back' link='/old' classNames={uSizeFull} />
        {geoMapDisplay}
      </div>
    );
  }
});

render(
	<IndexUser2 />,
	document.getElementById('index-user2')
);