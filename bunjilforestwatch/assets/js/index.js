import { render } from 'react-dom';
import React from 'react';

import App from './app';

var AppComponent = React.createClass({
  render() {
    return (
      <div class='testMeNao'>
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