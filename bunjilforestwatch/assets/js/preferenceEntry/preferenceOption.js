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
    const { onSelect, children: region } = this.props;

    if (onSelect !== undefined) {
      onSelect(region, !this.state.selected);
    }

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
