import React from 'react';
import Request from 'superagent';
import { browserHistory } from 'react-router';

import { categories, categoryImages } from '../constants';
import Button from '../button';
import ToggleSwitch from '../toggleSwitch';
import Icon from '../icon';
import {uTextAlignCenter} from '../../stylesheets/utils';
import {
  container, categoryListItem, title,
  categoryButton, categoryOptionList,
  categoryIcon, lineSeparator, preferenceIcon,
  preferenceButton, toggleSwitchCluster, toggleSwitchClusterLabel
} from '../../stylesheets/observationTask/votingTaskBar';

// TODO: Split the voting component and the toggle components into two seperate
//       components that live inside the parent task bar component
export default React.createClass({

  getInitialState() {
    return {
      selectionMade: false
    };
  },

  componentWillReceiveProps(nextProps) {
    this.setState({
      selectionMade: false
    });
  },

  getTaskDuration() {
    const { taskStartTime } = this.props;

    if (!taskStartTime) { return 0; }

    // Original time - current time, convert from milliseconds to seconds
    return Math.abs((taskStartTime - Date.now())) / 1000;
  },

  votingHandler({target: {innerText}}) {
    let self = this;
    if (self.state.selectionMade !== undefined && self.state.selectionMade === false) {
      if (!categories.includes(innerText) || !this.props.caseId) {
        return;
      }
      // Should output or provide visual cue that an error has occurred

      let payload = {
        case_id: this.props.caseId,
        vote_category: innerText.toUpperCase(),
        task_duration_seconds: this.getTaskDuration()
      };

      Request
        .post('/observation-task/response')
        .send(payload)
        .set('Accept', 'application/json')
        .end(
          function (err, res) {
            // Intermittently fails here, placing a log to capture the issue
            console.log(err);
            console.log(res);

            // Should output or provide visual cue that an error has occurred
            if (err == null && res.ok) {
              self.props.setSelectedCategory(payload.vote_category);
            }
          }
        );

      self.setState({selectionMade: true});
    }
  },

  clusterToggleHandler({ target }) {
    // Event is fired off twice, oddly first is undefined
    if (target.checked != true && target.checked != false) { return; }
    if (!this.props.setDisplayClusters) { return; }

    this.props.setDisplayClusters(target.checked);
  },

  renderCategoryList() {
    let categoryList = categories.map((category, index) => {
      return (
        <li key={index} className={categoryListItem} onClick={this.votingHandler}>
          <Button classNames={categoryButton}>
            <Icon classNames={categoryIcon} src={categoryImages[category]}/>
            {category}
          </Button>
        </li>
      );
    });

    return <ul className={categoryOptionList}>{categoryList}</ul>;
  },

  renderClusterToggle() {
    return (
      <ToggleSwitch
        onClick={this.clusterToggleHandler}
        defaultChecked={true}
        classNames={toggleSwitchCluster}>

        <p className={toggleSwitchClusterLabel}>
          Display alerts
        </p>

      </ToggleSwitch>
    );
  },

  renderPreferenceSetting() {
    const cogwheelSrc = require('../../images/cogwheel.png');
    const routeToPreference = () => browserHistory.push('/observation-task/preference');

    return (
      <Button classNames={preferenceButton} onClick={routeToPreference}>
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
        {this.renderClusterToggle()}
        <span className={lineSeparator} />
        {this.renderPreferenceSetting()}
      </div>
    );
  }
});
