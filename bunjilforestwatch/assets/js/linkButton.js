import React from 'react';

import classNames from 'classnames';

export default React.createClass({
  render() {
  	let classNames({
  		`LinkButton`: true,
  		 `${this.props.classNames}`: !!this.props.classNames
  	});

    return (
      <a className={classNames} href={this.props.link}>
      	{this.props.name}
      </a>
    );
  }
});
