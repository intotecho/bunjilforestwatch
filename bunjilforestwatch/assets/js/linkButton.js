import React from 'react';

export default React.createClass({
  render() {
  	let classNames = `LinkButton ${this.props.classNames}`;

    return (
      <a className={classNames} href={this.props.link}>
      	{this.props.name}
      </a>
    );
  }
});
