import React from 'react';

import Request from 'superagent';

import { container, categoryLink, title } from '../../stylesheets/observationTask/votingTaskBar';
import { uTextAlignCenter } from '../../stylesheets/utils';

// FIXME: Make this an open constant somewhere
const categoryList = ['Fire', 'Deforestation', 'Agriculture', 'Road', 'Unsure'];

export default React.createClass({
	votingHandler({ target: { innerText } }) {
		// Should output or provide visual cue that an error has occurred
		if (!categoryList.includes(innerText) || !this.props.caseId) { return; }

		const self = this;
		const payload = {
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

	renderCategoryLinkList() {
		const categoryLinkList = categoryList.map((category, index) => {
			return 	<li key={index} className={categoryLink}>
								<button onClick={this.votingHandler}>{category}</button>
							</li>;
		});

		return <ul>{categoryLinkList}</ul>;
	},

  render() {
  	const titleClasses = `${title} ${uTextAlignCenter}`;

    return (
      <div className={container}>
      	<p className={titleClasses}>Category</p>
      	{this.renderCategoryLinkList()}
      </div>
    );
  }
});
