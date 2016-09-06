import React from 'react';

import Request from 'superagent';
import classNames from 'classnames';

import { navBar, navList } from '../../stylesheets/navBar/navBar';

const NAVIGATIONS = {
  'home': '/old',
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
        <li className={navList}>
          <a href={NAVIGATIONS[key]}>
            {key}
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
