import React from 'react';
import Request from 'superagent';

import Button from '../button';
import Icon from '../icon';
import { categories, categoryImages } from '../constants';
import { uTextAlignCenter } from '../../stylesheets/utils';
import {
  container, categoryListItem, title,
  categoryButton, categoryOptionList,
  categoryIcon, lineSeparator, preferenceIcon,
  preferenceButton
} from '../../stylesheets/observationTask/votingTaskBar';

export default React.createClass({
  votingHandler({ target: { innerText } }) {
    // Should output or provide visual cue that an error has occurred
    if (!categories.includes(innerText) || !this.props.caseId) { return; }

    let self = this;
    let payload = {
      case_id: this.props.caseId,
      vote_category: innerText.toUpperCase()
    };

    Request
    .post('/observation-task/response')
    .send(payload)
    .set('Accept', 'application/json')
    .end(
      function(err, res) {
        // Interminently fails here, placing a log to capture the issue
        console.log(err);
        console.log(res);

        // Should output or provide visual cue that an error has occurred
        if (err == null && res.ok) {
          self.props.setNextTask();
        }
      }
    );
  },

  renderCategoryList() {
    let categoryList = categories.map((category, index) => {
      return  (
        <li key={index} className={categoryListItem} onClick={this.votingHandler}>
          <Button classNames={categoryButton}>
            <Icon classNames={categoryIcon} src={categoryImages[category]} />
            {category}
          </Button>
        </li>
      );
    });

    return <ul className={categoryOptionList}>{categoryList}</ul>;
  },

  renderPreferenceSetting() {
    const cogwheelSrc = require('../../images/cogwheel.png');

    return (
      <Button classNames={preferenceButton}>
        <Icon classNames={preferenceIcon} src={cogwheelSrc} />
        Preference
      </Button>
    );
  },

  render() {
    const titleClasses = `${title} ${uTextAlignCenter}`;

    return (
      <div className={container}>
        <p className={titleClasses}>Category</p>
        {this.renderCategoryList()}
        <span className={lineSeparator} />
        {this.renderPreferenceSetting()}
      </div>
    );
  }
});
