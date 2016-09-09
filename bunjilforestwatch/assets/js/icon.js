import React from 'react';
import classNames from 'classnames';

import { Icon } from '../stylesheets/icon';

export default React.createClass({
  render() {
    let iconClasses = classNames({
      [`${Icon}`]: true,
       [`${this.props.classNames}`]: !!this.props.classNames
    });

    return (
      <img src={this.props.src} className={iconClasses}>
        {this.props.children}
      </img>
    );
  }
});
