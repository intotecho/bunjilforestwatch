import { render } from 'react-dom';
import React from 'react';

import App from './app';
import { hello, sample } from '../stylesheets/index';

var AppComponent = React.createClass({
  render() {
    return (
      <div className={sample}>
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