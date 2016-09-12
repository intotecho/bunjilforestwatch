import React from 'react';
import _ from 'lodash';
import {
  container, positive, negative, neutral
} from '../../stylesheets/observationTask/consensusMessage';

require('velocity-animate');
require('velocity-animate/velocity.ui');
var snabbt = require('snabbt.js');

const MESSAGE_DURATION_MS = 5000;

export default React.createClass({

  componentDidMount(prevProps, prevState) {
    if (this.refs.popMsg !== undefined) {
      Velocity(this.refs.popMsg,
        {opacity: 0}, {easing: "ease-out", duration: 1000, delay: 3500});
      snabbt(this.refs.popMsg, {
        position: [0, -75, 0],
        // easing: 'easeIn',
        opacity: [0],
        duration: 4400
      });
    }
  },

  findHighest(listOfVotes) {
    let currentHighestCategory = Object.keys(listOfVotes)[0];
    let currentHighestNumberOfVotes = listOfVotes[currentHighestCategory];
    for (var category in listOfVotes) {
      var votesForCategory = listOfVotes[category];
      if (currentHighestNumberOfVotes < votesForCategory) {
        currentHighestCategory = category;
        currentHighestNumberOfVotes = votesForCategory;
      }
    }
    return currentHighestCategory;
  },

  getMostSelected() {
    const {props} = this;
    return this.findHighest(props.caseVotes);
  },

  getSecondMostSelected() {
    const {props} = this;
    return this.findHighest(_.omit(props.caseVotes, this.getMostSelected()));
  },

  convertToPercentage(votes, totalVotes) {
    return _.floor((votes / totalVotes) * 100, 1);
  },

  renderMessage() {
    const {props} = this;
    let msg1, msg2;
    let colourClass;

    let totalVotes = _.sum(_.values(props.caseVotes));
    if (totalVotes === 0) {
      msg1 = "You are the first to vote on this issue";
      msg2 = "";
      colourClass = neutral;
    } else {
      let percentThatAgreedWithYou = this.convertToPercentage(props.caseVotes[props.selectedCategory], totalVotes);

      let mostSelectedCategory = this.getMostSelected();
      let percentForMostSelected = this.convertToPercentage(props.caseVotes[mostSelectedCategory], totalVotes);

      let secondMostSelectedCategory = this.getSecondMostSelected();
      let percentForSecondMostSelected = this.convertToPercentage(props.caseVotes[secondMostSelectedCategory], totalVotes);

      let opposingCategory, percentForOpposingCategory;
      if (props.selectedCategory !== mostSelectedCategory) {
        opposingCategory = _.upperFirst(mostSelectedCategory);
        percentForOpposingCategory = percentForMostSelected;
      } else {
        opposingCategory = _.upperFirst(secondMostSelectedCategory);
        percentForOpposingCategory = percentForSecondMostSelected;
      }
      if (Math.abs(percentThatAgreedWithYou - percentForOpposingCategory) <= 10) {
        msg1 = percentThatAgreedWithYou + '% agreed with you';
        msg2 = percentForOpposingCategory + '% chose ' + opposingCategory;

        colourClass = neutral;
      } else if (percentThatAgreedWithYou > percentForOpposingCategory) {
        msg1 = percentThatAgreedWithYou + '% agreed with you';
        msg2 = percentForOpposingCategory > 0.01 ? percentForOpposingCategory + '% chose ' + opposingCategory : '';

        colourClass = positive;
      } else {
        msg1 = percentForOpposingCategory + '% chose ' + opposingCategory;
        msg2 = percentThatAgreedWithYou > 0.01 ? percentThatAgreedWithYou + '% agreed with you' : '';

        colourClass = negative;
      }
    }
    setTimeout(() => this.props.startNextTask(), MESSAGE_DURATION_MS);
    return (
      <div ref='popMsg' className={container}>
        <p className={colourClass}>{msg1}</p>
        <p className={colourClass}>{msg2}</p>
      </div>
    );
  },

  render() {
    return (
      <div>
        {this.renderMessage()}
      </div>
    );
  }
});