import React from 'react';

import classNames from 'classnames';

export default React.createClass({
  render() {
  	let linkButtonClasses = classNames({
  		'LinkButton': true,
  		 [`${this.props.classNames}`]: !!this.props.classNames
  	});

    return (
      <a className={linkButtonClasses} href={this.props.link}>
      	{this.props.name}
      </a>
    );
  }
});
