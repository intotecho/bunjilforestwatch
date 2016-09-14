import React from 'react';
import classNames from 'classnames';

export default React.createClass({
  render() {
  	const buttonClasses = classNames({
  		'Button': true,
  		 [`${this.props.classNames}`]: !!this.props.classNames
  	});

    let button = <button className={buttonClasses} onClick={this.props.onClick}>
                   {this.props.children}
                 </button>;

    // Reasoning (Super hack)
    //  I don't want to define a private method that calls superagent
    //  I'd rather encapsulate it an in anchor tag and redirect that way
    if (this.props.link !== undefined) {
      button = <a href={this.props.link}>{button}</a>;
    }

    return button;
  }
});
