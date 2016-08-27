import { render } from 'react-dom';
import React from 'react';

import LinkButton from './linkButton';
import GeoMapDisplay from './geoMapDisplay';

import { hello } from '../stylesheets/indexUser2';
import { uSizeFull } from '../stylesheets/utils';

var IndexUser2 = React.createClass({
  render() {
    return (
      <div>
        <LinkButton name='Back' link='/old' classNames={uSizeFull} />

        <GeoMapDisplay />
      </div>
    );
  }
});

render(
	<IndexUser2 />,
	document.getElementById('index-user2')
);