import { render } from 'react-dom';
import React from 'react';

import App from './app';
import { hello } from '../css/index'

var AppComponent = React.createClass({
  render() {
    return (
      <div className={hello}>
      	hello
      	<App />
      </div>
    );
  }
});

render(
	<AppComponent />,
	document.getElementById('index-user2')
);