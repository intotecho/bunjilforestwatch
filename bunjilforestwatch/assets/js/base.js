import React from 'react'
import { render } from 'react-dom'
import { Router, Route, Link, browserHistory } from 'react-router'

import IndexUser2 from './observationTask/IndexUser2';

render((
  <Router history={browserHistory}>
    <Route path="/" component={IndexUser2}>
      <Route path="*" component={IndexUser2} />
    </Route>
  </Router>
), document.getElementById('bfw-baseEntry-react'))