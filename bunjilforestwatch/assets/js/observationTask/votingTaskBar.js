import React from 'react';

import Request from 'superagent';
import Button from '../button';
import Icon from '../icon';

import { uTextAlignCenter } from '../../stylesheets/utils';
import { container, categoryListItem, title,
         categoryButton, categoryOptionList,
         categoryIcon } from '../../stylesheets/observationTask/votingTaskBar';

// FIXME: Make this an open constant somewhere
const CATEGORIES = ['Fire', 'Deforestation', 'Agriculture', 'Road', 'Unsure'];
const categoryImages = {
  'Fire':          require('../../images/fire.png'),
  'Deforestation': require('../../images/deforestation.png'),
  'Agriculture':   require('../../images/agriculture.png'),
  'Road':          require('../../images/road.png'),
  'Unsure':        require('../../images/unsure.png'),
}

export default React.createClass({
	votingHandler({ target: { innerText } }) {
		// Should output or provide visual cue that an error has occurred
		if (!CATEGORIES.includes(innerText) || !this.props.caseId) { return; }

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
	  		// Should output or provide visual cue that an error has occurred
	  		if (err == null && res.ok) {
					self.props.setNextTask();
	  		}
	  	}
	  );
	},

	renderCategoryList() {
		let categoryList = CATEGORIES.map((category, index) => {
			return 	<li key={index} className={categoryListItem}>
								<Button classNames={categoryButton} onClick={this.votingHandler}>
                  <Icon classNames={categoryIcon} src={categoryImages[category]} />
                  {category}
                </Button>
							</li>;
		});

		return <ul className={categoryOptionList}>{categoryList}</ul>;
	},

  render() {
  	let titleClasses = `${title} ${uTextAlignCenter}`;

    return (
      <div className={container}>
      	<p className={titleClasses}>Category</p>
      	{this.renderCategoryList()}
      </div>
    );
  }
});
