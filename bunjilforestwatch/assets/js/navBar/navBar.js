import React from 'react';

import Request from 'superagent';
import _ from 'lodash';
import classNames from 'classnames';

import { navBar, navList } from '../../stylesheets/navBar/navBar';

const NAVIGATIONS = {
  'home': '/',
  'glad': 'glad',
  'about': '',
  'areas': '',
  'tasks': '',
  'journals': ''
};

export default React.createClass({
  renderNavigationsList() {
    let navigationsList = [];

    for (let key in NAVIGATIONS) {
      navigationsList.push(
        <li key={key} className={navList}>
          <a href={NAVIGATIONS[key]}>
            {_.capitalize(key)}
          </a>
        </li>
      );
    }

    return navigationsList;
  },

  render() {
    return (
      <ul className={navBar}>
        {this.renderNavigationsList()}
      </ul>
    );
  }
});
