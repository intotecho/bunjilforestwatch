import {render} from 'react-dom';
import React from 'react';
import _ from 'lodash';
import NavBar from '../navBar/navBar';
import VotingTaskBar from './votingTaskBar';
import GeoMapDisplay from './geoMapDisplay';
import ConsensusMessage from './consensusMessage'
import Request from 'superagent';

import {uSizeFull} from '../../stylesheets/utils';

var IndexUser2 = React.createClass({
  getInitialState() {
    this.startNextTask(); // Renders twice still super crappy

    return {
      selectedCategory: null,
      areaId: -1,
      case: {},
      gladCluster: {}
    };
  },
  
  setSelectedCategory(selectedCategory) {
    this.setState({
      selectedCategory: selectedCategory
    });
  },
  
  startNextTask() {
    const self = this;

    // Fire off get request before component starts rendering
    Request
      .get('/observation-task/next')
      .end(
        function (err, res) {
          if (err === null && res.ok) {
            // Response is coming back as JSON string
            const response = JSON.parse(res.text);
            const gc = response.glad_cluster;
            console.log("response received");
            self.setState({
              areaId: response.area_id,
              selectedCategory: null,
              case: response.case,
              gladCluster: gc
            });
          }
        }
      );
  },

  renderVotingTaskBar() {
    const {state, setSelectedCategory} = this;
    if (_.isEmpty(state.case) === false) {
      console.log("rendeing task bar");
      return <VotingTaskBar setSelectedCategory={setSelectedCategory} caseId={state.case.case_id}/>;
    }
    return null;
  },

  renderGeoMapDisplay() {
    const {state} = this;
    if (_.isEmpty(state.gladCluster) === false) {
      console.log(state.gladCluster.geojson);
      const features = state.gladCluster.geojson.features;
      const coords = features[0].properties.points.coordinates[0];
      const long = coords[0];
      const lat = coords[1];
      console.log("rendeing map");
      return <GeoMapDisplay features={features} long={long} lat={lat}/>;
    }

    return null; // TODO: have the map object have a default no features available view
  },

  renderConsensusMessage() {
    const {state} = this;
    if (state.selectedCategory !== null) {
      console.log("rendering message");
      return <ConsensusMessage startNextTask={this.startNextTask} selectedCategory={state.selectedCategory.toLowerCase()}
                                           caseVotes={state.case.votes}/>;
    }
    return null;
  },
  
  render() {
    let votingTaskBar, geoMapDisplay, consensusMessage;
    votingTaskBar = this.renderVotingTaskBar();
    geoMapDisplay = this.renderGeoMapDisplay();
    consensusMessage = this.renderConsensusMessage();

    return (
      <div>
        <NavBar />
        {votingTaskBar}
        {geoMapDisplay}
        {consensusMessage}
      </div>
    );
  }
});

render(
  <IndexUser2 />,
  document.getElementById('index-user2')
);