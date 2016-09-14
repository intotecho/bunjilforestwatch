import React from 'react'
import { render } from 'react-dom'
import { Router, IndexRoute, Route, Link, browserHistory } from 'react-router'

import NavBar from './navBar/navBar';
import IndexUser2 from './observationTask/IndexUser2';
import PreferenceEntry from './preferenceEntry/preferenceEntry';

const App = React.createClass({
  render() {
    return (
      <div>
        <NavBar />
        {this.props.children}
      </div>
    );
  }
});

render((
  <Router history={browserHistory}>
    <Route path="/" component={App}>
      <IndexRoute component={IndexUser2} />
      <Route path="observation-task/preference" component={PreferenceEntry} />
    </Route>
  </Router>
), document.getElementById('bfw-baseEntry-react'))