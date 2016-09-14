import { render } from 'react-dom';
import React from 'react';
import classNames from 'classnames';
import _ from 'lodash';

import {
  container, imageContainer, selected
} from '../../stylesheets/preferenceEntry/preferenceOption';

export default React.createClass({
  getInitialState() {
    return {
      selected: false
    };
  },

  setSelected() {
    this.setState({
      selected: !this.state.selected
    });
  },

  render() {
    const containerClasses = classNames({
      [`${container}`]: true,
      [`${selected}`]: this.state.selected
    });

    return (
      <div className={containerClasses} onClick={this.setSelected}>
        <img className={imageContainer} src={this.props.image} />
        {_.capitalize(this.props.children)}
      </div>
    );
  }
});
