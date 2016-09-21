import React from 'react'
import { render } from 'react-dom'
import { Router, IndexRoute, Route, Link, browserHistory } from 'react-router'

import NavBar from './navBar/navBar';
import ObservationTask from './observationTask/observationTask';
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
      <IndexRoute component={ObservationTask} />
      <Route path="observation-task/preference" component={PreferenceEntry} />
    </Route>
  </Router>
), document.getElementById('bfw-baseEntry-react'))