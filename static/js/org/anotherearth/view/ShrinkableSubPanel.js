//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

org.anotherearth.view.ShrinkableSubPanel = function(title, subPanelId) {
	//private variables
	var subPanel, subPanelHead, subPanelBody, shrinkingIcon;
	var title = title;
	var subPanelId = subPanelId;
	var subPanelObjects = new org.anotherearth.util.ArrayList();
	var self = this;
	var isSlideInProgress = false;//prevents two concurrent closing commands from leaving an empty, open subpanel

	//privileged methods
	this.close = function() {
		if (isSlideInProgress) {
			return;
		}
		var _turnOffSlideFlag = function() {
			isSlideInProgress = false;
		};
		isSlideInProgress = true;
		var iterator = self.createIterator();
		if ($(subPanelBody).css('display') === 'none') {
			while (iterator.hasNext()) {
				iterator.next().show();
			}
			$(subPanelBody).slideToggle(175, _turnOffSlideFlag);
		}
		else if ($(subPanelBody).css('display') !== 'none') {
			var _hider = function() {
				while (iterator.hasNext()) {
					iterator.next().hide();
				}
				_turnOffSlideFlag();
			};
			$(subPanelBody).slideToggle(175, _hider);
		}
		$(shrinkingIcon).toggleClass(org.anotherearth.SUB_PANEL_SHUT_ICON_CLASS).toggleClass(org.anotherearth.SUB_PANEL_OPEN_ICON_CLASS);
		return false;//else page reloads - suppressing default button action
	};
	this.createGUIElements = function() {
		shrinkingIcon	= document.createElement('span');
		$(shrinkingIcon).addClass(org.anotherearth.SUB_PANEL_CAPTION_BUTTON_CLASS).addClass('ui-icon').addClass(org.anotherearth.SUB_PANEL_OPEN_ICON_CLASS);

		subPanel = document.createElement('div');
		subPanel.id = subPanelId;
		$(subPanel).addClass('sub_panel');
		
		subPanelHead = document.createElement('h5');
		$(subPanelHead).addClass('sub_panel_header');
		$(subPanelHead).click(this.close);
		$(subPanelHead).bind('mouseleave mouseenter', function() {
			$(this).toggleClass('sub_panel_header_highlight');
		});

		subPanelBody = document.createElement('div');
		$(subPanelBody).addClass('sub_panel_body');
	
		var titleContainer = document.createElement('span');
		titleContainer.appendChild(document.createTextNode(title));
		$(titleContainer).addClass('sub_panel_title');
		
		subPanelHead.appendChild(shrinkingIcon);
		subPanelHead.appendChild(titleContainer);
		subPanel.appendChild(subPanelHead);
		subPanel.appendChild(subPanelBody);
		subPanel.style.display = 'none';
	};
	this.addChild = function(subPanelObject) {
		//org.anotherearth.util.Interface.ensureImplements(subPanelObject, org.anotherearth.GUIComposite, org.anotherearth.GUIObject);
		subPanelObjects.add(subPanelObject);
		subPanelBody.appendChild(subPanelObject.getContainingElement());
	};
	this.createIterator = function() {
		return subPanelObjects.iterator();
	};
	this.removeChild = function(subPanelObject) {
		subPanelObjects.remove(subPanelObjects.getIndexOf(subPanelObject));
	};
	this.setTabIndex = function(tabIndex) {//Do nothing with this, and return tabIndex as supplied to indicate that nothing has been done.
		return tabIndex;
	};
	this.show = function() {
		var _showShrinkingIcon = function() {
			shrinkingIcon.style.visibility = 'visible';
		};
		subPanel.style.display = 'block';
		shrinkingIcon.style.visibility = 'hidden';
		setTimeout(_showShrinkingIcon, 70);//bit of a hack to stop icons appearing before the rest of the (sliding) panel
	};
	this.hide = function() {
		subPanel.style.display = 'none';
	};
	this.getContainingElement = function() {
		return subPanel;
	};

	//constructor
	this.createGUIElements();
};
org.anotherearth.view.ShrinkableSubPanel.prototype = {
	performNewEarthPropsUpdate: function() {},
	performUndoRedoUpdate: function() {}
};
