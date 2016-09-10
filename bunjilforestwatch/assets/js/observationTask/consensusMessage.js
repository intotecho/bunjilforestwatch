import React from 'react';
import {
  container, positive, negative, neutral
}
  from '../../stylesheets/observationTask/consensusMessage.scss';

require('velocity-animate');
require('velocity-animate/velocity.ui');
var snabbt = require('snabbt.js');

const CATEGORIES = ['Fire', 'Deforestation', 'Agriculture', 'Road', 'Unsure'];

const MESSAGE_DURATION_MS = 5000;

export default React.createClass({

  componentDidUpdate: function () {
    if (this.refs.popMsg != undefined) {
      Velocity(this.refs.popMsg,
        {opacity: 0}, {easing: "ease-out", duration: 1000, delay: 3500});
      Snabbt(this.refs.popMsg, {
        position: [0, -75, 0],
        // easing: 'easeIn',
        opacity: [0],
        duration: 4400
      });
    }
  },

  renderMessage() {
    console.log("MSG");
    let msg1, msg2;
    let value1, value2;
    let opposingChoice = 'Fire';
    let classColour;

    value1 = Math.round(Math.random() * 100);
    value2 = Math.round(Math.random() * (100 - value1));

    if (value2 == 0) {
      value2 += 1;
    } // TODO: consider removing this

    if (Math.abs(value1 - value2) <= 10) {
      msg1 = value1 + '% agreed with you';
      msg2 = value2 + '% chose ' + opposingChoice;

      classColour = 'neutral';
    } else if (value1 > value2) {
      msg1 = value1 + '% agreed with you';
      msg2 = value2 + '% chose ' + opposingChoice;
      
      classColour = 'positive';
    } else {
      msg1 = value2 + '% chose ' + opposingChoice;
      msg2 = value1 + '% agreed with you';

      classColour = 'negative';
    }
    
    setTimeout(() => this.props.startNextTask(), MESSAGE_DURATION_MS);

    return (
      <div ref='popMsg' className={container}>
        <p className={classColour}>{msg1}</p>
        <p className={classColour}>{msg2}</p>
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