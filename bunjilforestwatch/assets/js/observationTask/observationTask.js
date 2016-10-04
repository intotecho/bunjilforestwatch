import {render} from 'react-dom';
import React from 'react';
import _ from 'lodash';
import VotingTaskBar from './votingTaskBar';
import GeoMapDisplay from './geoMapDisplay';
import ConsensusMessage from './consensusMessage'
import Request from 'superagent';

import {uSizeFull} from '../../stylesheets/utils';

export default React.createClass({
  getInitialState() {
    return {
      selectedCategory: null,
      areaId: -1,
      case: {},
      gladCluster: {}
    };
  },

  componentWillMount() {
    this.startNextTask();
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

            self.setState({
              areaId: response.area_id,
              selectedCategory: null,
              case: response.case,
              gladCluster: response.glad_cluster,
              overlays: response.overlays
            });
          }
        }
      );
  },

  renderVotingTaskBar() {
    const {state, setSelectedCategory} = this;

    if (_.isEmpty(state.case) === false) {
      return (
        <VotingTaskBar
          taskStartTime={Date.now()}
          setSelectedCategory={setSelectedCategory}
          caseId={state.case.case_id}
        />
      );
    }

    return;
  },

  renderGeoMapDisplay() {
    const { gladCluster, overlays } = this.state;

    if (_.isEmpty(gladCluster) === false) {
      const features = gladCluster.geojson.features;
      const coords = features[0].properties.points.coordinates[0];
      const long = coords[0];
      const lat = coords[1];

      return (
        <GeoMapDisplay
          overlays={overlays}
          clusterId={gladCluster.cluster_id}
          features={features}
          long={long}
          lat={lat}
        />
      );
    }

    return; // TODO: have the map object have a default no features available view
  },

  renderConsensusMessage() {
    const {state} = this;

    if (state.selectedCategory !== null) {
      return <ConsensusMessage
                startNextTask={this.startNextTask}
                selectedCategory={state.selectedCategory.toLowerCase()}
                caseVotes={state.case.votes}
            />;
    }

    return;
  },

  render() {
    const votingTaskBar = this.renderVotingTaskBar();
    const geoMapDisplay = this.renderGeoMapDisplay();
    const consensusMessage = this.renderConsensusMessage();

    return (
      <div>
        {votingTaskBar}
        {geoMapDisplay}
        {consensusMessage}
      </div>
    );
  }
});