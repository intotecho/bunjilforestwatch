import { render } from 'react-dom';
import React from 'react';
import { browserHistory } from 'react-router'
import _ from 'lodash';
import Request from 'superagent';

import Button from '../button';
import PreferenceOption from './preferenceOption';
import { regionPreference } from '../constants';
import {
  container, title, regionContainer, btnContinue
} from '../../stylesheets/preferenceEntry/preferenceEntry';

export default React.createClass({
  componentDidMount() {
    const self = this;
    let selectedOptions = [];
    let regionData = [];

    Request
    .get('/observation-task/preference/resource')
    .set('Accept', 'application/json')
    .end(
      function (err, res) {
        if (err == null && res.ok) {
          const preference = JSON.parse(res.text);

          if (preference.has_preference) {
            selectedOptions = preference.region_preference;
          }

          // Initiate another request inside callback to retain selectedOptions
          Request
          .get('/region')
          .set('Accept', 'application/json')
          .end(
            function (err, res) {
              if (err == null && res.ok) {
                self.setState({
                  selectedOptions: selectedOptions,
                  regionData: JSON.parse(res.text).region_data
                });
              }
            }
          );
        }
      }
    );

  },

  getInitialState() {
    return {
      selectedOptions: [],
      regionData: []
    };
  },

  updateSelectedOptions(region, shouldInclude) {
    let { selectedOptions } = this.state;

    if (shouldInclude) {
      if (!_.includes(selectedOptions, region)) {
        selectedOptions.push(region);
      }
    } else {
      selectedOptions = _.reject(selectedOptions, (selectedRegion) => {
        return selectedRegion == region;
      });
    }

    this.setState({
      selectedOptions: selectedOptions
    });
  },

  submitHandler() {
    // FIXME: Stop hitting remote endpoint when theres no difference in selection

    const payload = {
      region_preference: this.state.selectedOptions
    };

    Request
    .post('/observation-task/preference/resource')
    .send(payload)
    .set('Accept', 'application/json')
    .end(
      function(err, res) {
        // Should output or provide visual cue that an error has occurred
        if (err == null && res.ok) {
          browserHistory.push('/');
        }
      }
    );
  },

  renderPreferenceChoice() {
    const { regionData } = this.state;

    return _.map(regionData, (region) => {
      const { region_id, region_name } = region;

      return (
        <PreferenceOption
          key={region_id}
          selected={_.includes(this.state.selectedOptions, region_name)}
          onSelect={this.updateSelectedOptions}
          image={regionPreference[region_name]}>
          {region_name}
        </PreferenceOption>
      );
    });
  },

  render() {
    return (
      <div className={container}>
        <p className={title}>Select the regions you want to watch</p>
        <div className={regionContainer}>{this.renderPreferenceChoice()}</div>
        <Button
          classNames={btnContinue}
          onClick={this.submitHandler}>
          Continue
        </Button>
      </div>
    );
  }
});
