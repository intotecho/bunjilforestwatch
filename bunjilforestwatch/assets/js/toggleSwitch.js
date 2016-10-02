import React from 'react';
import classNames from 'classnames';

import {
  toggleSwitch, slider, round, checkbox
} from '../stylesheets/toggleSwitch';

export default React.createClass({
  render() {
    let toggleSwitchClasses = classNames({
      [`${toggleSwitch}`]: true,
      [`${this.props.classNames}`]: !!this.props.classNames
    });

    return (
      <label
        onClick={this.props.onClick}
        className={toggleSwitchClasses}>

        <input
          className={checkbox}
          type='checkbox'
          defaultChecked={this.props.defaultChecked}
        />

        <div className={`${slider} ${round}`} />
        {this.props.children}

      </label>
    );
  }
});
