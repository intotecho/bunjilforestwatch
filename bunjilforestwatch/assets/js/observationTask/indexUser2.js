import { render } from 'react-dom';
import React from 'react';

import LinkButton from '../linkButton';
import VotingTaskBar from './votingTaskBar';
import GeoMapDisplay from './geoMapDisplay';
import Request from 'superagent';

import { uSizeFull } from '../../stylesheets/utils';

var IndexUser2 = React.createClass({
  getInitialState() {
    return {
      isTaskReady: false,
      areaId: -1,
      case: {},
      gladCluster: {}
    };
  },

  setNextTask() {
    this.setState({
      isTaskReady: false
    });
  },

  render() {
    const { state, setNextTask } = this;
    let votingTaskBar, geoMapDisplay;

    if (state.isTaskReady === true) {
      // Ugly ultra hacky data retrieval
      const features = state.gladCluster.geojson.features;
      const coords = features[0].properties.points.coordinates[0];
      const long = coords[0];
      const lat = coords[1];

      votingTaskBar = <VotingTaskBar setNextTask={setNextTask} caseId={state.case.case_id} />;
      geoMapDisplay = <GeoMapDisplay features={features} long={long} lat={lat} />;
    } else {
      const self = this;

      // Fire off get request before component starts rendering
      Request
      .get('/observation-task/next')
      .end(
        function(err, res) {
          if (err === null && res.ok) {
            // Response is coming back as JSON string
            const response = JSON.parse(res.text);

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
        {votingTaskBar}
        {geoMapDisplay}
      </div>
    );
  }
});

render(
	<IndexUser2 />,
	document.getElementById('index-user2')
);