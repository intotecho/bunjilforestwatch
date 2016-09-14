import { render } from 'react-dom';
import React from 'react';
import { browserHistory } from 'react-router'
import _ from 'lodash';
import Request from 'superagent';

import Button from '../button';
import PreferenceOption from './preferenceOption';
import { regionPreference, regionPreferenceTest } from '../constants';

import {
  container, title, regionContainer, btnContinue
} from '../../stylesheets/preferenceEntry/preferenceEntry';

export default React.createClass({
  componentDidMount() {
    const self = this;

    Request
    .get('/observation-task/preference/resource')
    .set('Accept', 'application/json')
    .end(
      function (err, res) {
        if (err == null && res.ok) {
          const preference = JSON.parse(res.text);

          if (preference.has_preference) {
            self.setState({
              selectedOptions: preference.region_preference
            });
          }
        }
      }
    );
  },

  getInitialState() {
    return {
      selectedOptions: []
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
    return _.map(regionPreferenceTest, (value, key) => {
      return (
        <PreferenceOption
          key={key}
          selected={_.includes(this.state.selectedOptions, key)}
          onSelect={this.updateSelectedOptions}
          image={value}>
          {key}
        </PreferenceOption>
      );
    });
  },

  render() {
    return (
      <div className={container}>
        <p className={title}>Select the regions you prefer to be served a task</p>
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
