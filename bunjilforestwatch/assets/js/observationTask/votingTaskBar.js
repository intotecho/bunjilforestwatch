import React from 'react';

import Request from 'superagent';
import Button from '../button';
import Icon from '../icon';

import {uTextAlignCenter} from '../../stylesheets/utils';
import {
  container, categoryListItem, title,
  categoryButton, categoryOptionList,
  categoryIcon
} from '../../stylesheets/observationTask/votingTaskBar';

// FIXME: Make this an open constant somewhere
const CATEGORIES = ['Fire', 'Deforestation', 'Agriculture', 'Road', 'Unsure'];
const categoryImages = {
  'Fire': require('../../images/fire.png'),
  'Deforestation': require('../../images/deforestation.png'),
  'Agriculture': require('../../images/agriculture.png'),
  'Road': require('../../images/road.png'),
  'Unsure': require('../../images/unsure.png')
};

export default React.createClass({

  getInitialState() {
    console.log("VTB init state");
    return {
      selectionMade: false
    };
  },

  componentWillReceiveProps(nextProps) {
    console.log("VTB props change: " + nextProps.caseId);
    this.setState({
      selectionMade: false
    });
  },

  votingHandler({target: {innerText}}) {
    let self = this;
    console.log(this.state.selectionMade + " for case " + this.props.caseId);
    if (self.state.selectionMade !== undefined && self.state.selectionMade === false) {
      if (!CATEGORIES.includes(innerText) || !this.props.caseId) {
        return;
      }
      // Should output or provide visual cue that an error has occurred

      let payload = {
        case_id: this.props.caseId,
        vote_category: innerText.toUpperCase()
      };

      Request
        .post('/observation-task/response')
        .send(payload)
        .set('Accept', 'application/json')
        .end(
          function (err, res) {
            // Interminently fails here, placing a log to capture the issue
            console.log(err);
            console.log(res);

            // Should output or provide visual cue that an error has occurred
            if (err == null && res.ok) {
              console.log("vtb " + payload.vote_category);
              self.props.setSelectedCategory(payload.vote_category);
              // self.props.setSelectedCategory();
            }
          }
        );

      self.setState({
          selectionMade: true
        }
      );
    }
  },

  renderCategoryList() {
    let categoryList = CATEGORIES.map((category, index) => {
      return <li key={index} className={categoryListItem} onClick={this.votingHandler}>
        <Button classNames={categoryButton}>
          <Icon classNames={categoryIcon} src={categoryImages[category]}/>
          {category}
        </Button>
      </li>;
    });

    return <ul className={categoryOptionList}>{categoryList}</ul>;
  },

  render() {
    const titleClasses = `${title} ${uTextAlignCenter}`;

    return (
      <div className={container}>
        <p className={titleClasses}>Category</p>
        {this.renderCategoryList()}
      </div>
    );
  }
});
