import { render } from 'react-dom';
import React from 'react';

import _ from 'lodash';
import Button from '../button';
import PreferenceOption from './preferenceOption';
import { regionPreference, regionPreferenceTest } from '../constants';

import {
  container, title, regionContainer, btnContinue
} from '../../stylesheets/preferenceEntry/preferenceEntry';

export default React.createClass({
  renderPreferenceChoice() {
    return _.map(regionPreferenceTest, (value, key) => {
      return  <PreferenceOption key={key} image={value}>
                {key}
              </PreferenceOption>;
    });
  },

  render() {
    return (
      <div className={container}>
        <p className={title}>Select the regions you prefer to be served a task</p>
        <div className={regionContainer}>{this.renderPreferenceChoice()}</div>
        <Button classNames={btnContinue}>Continue</Button>
      </div>
    );
  }
});
