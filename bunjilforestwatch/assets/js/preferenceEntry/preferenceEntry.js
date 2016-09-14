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
    const payload = {
      region_preference: this.state.selectedOptions
    };

    Request
    .post('/obsTaskPreference')
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
