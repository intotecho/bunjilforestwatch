//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

//Composite pattern leaf class
//implements GUIWidget and by extension GUIObject, TwoEarthsObserver and GUIComposite
org.anotherearth.view.SearchBox = function(earth, earthsController, searchBoxId, searchBoxTitle) {
	//private variable
	var searchBox;
	var earth = earth;
	var earthsController = earthsController;
	var title = searchBoxTitle;
	var undoRedoUpdateStrategy, newEarthPropsUpdateStrategy;

	//privileged methods
	this.createGUIElements = function() {
		searchBox = document.createElement('div');
		searchBox.id = searchBoxId;
		$(searchBox).addClass(org.anotherearth.SEARCH_BOX_CLASS);
		
		var boxTitle = document.createElement('h6');
		boxTitle.appendChild(document.createTextNode(title));
		$(boxTitle).addClass('search_box_label');
		
		var searcher = new google.search.LocalSearch();
		searcher.setNoHtmlGeneration();
		var searchControl = new google.search.SearchControl();
		searchControl.setSearchCompleteCallback(null, function() {
			$('.gs-title').removeAttr('href').css('text-decoration', 'none');//excuse the hacking - no google search box for earth plugin at this point in time 
			$('.gs-directions').remove();      
			var lat, lng;
			if (searcher.results.length && searcher.results[0].GsearchResultClass === GlocalSearch.RESULT_CLASS) {
				lat = parseFloat(searcher.results[0].lat);
				lng = parseFloat(searcher.results[0].lng);
				var props = earth.getProperties();
				earthsController.jumpCameraCoords(earth, lat, lng, 20000, props.tilt, props.head, props.date);
			}
		});
		searchControl.addSearcher(searcher);
		searchControl.draw(searchBox);
		searchBox.insertBefore(boxTitle, searchBox.firstChild);

		searchBox.style.display = 'none';
	};
	this.createIterator = function() {//null Iterator
		return {next:    function() { return null;  },
		        hasNext: function() { return false; }
		}; 
	};
	this.getContainingElement = function() {
		return searchBox;
	};
	this.show = function() {
		$('.gsc-branding-user-defined').siblings().andSelf().remove();
		searchBox.style.display = 'block';	
	};
	this.hide = function() {
		searchBox.style.display = 'none';
	};
	this.performUndoRedoUpdate = function() {
		undoRedoUpdateStrategy.execute(this);
	};
	this.performNewEarthPropsUpdate = function() {
		newEarthPropsUpdateStrategy.execute(this);
	};
	this.setTabIndex = function(tabIndex) {
		return tabIndex;
	};

	//contructor
	this.createGUIElements();
	undoRedoUpdateStrategy       = {execute: function(button) {} };
	newEarthPropsUpdateStrategy  = {execute: function(button) {} };
};
org.anotherearth.view.SearchBox.prototype = {
	addChild:    function() {},
	removeChild: function() {}
};
