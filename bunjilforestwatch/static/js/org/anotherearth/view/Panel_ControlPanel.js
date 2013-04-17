//file contains two classes, necessary as ControlPanel composed with Panel 

//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.view = window.org.anotherearth.view || {};

//Panel 'class' - with reference to the Composite design pattern, a composite class
//implements GUIComposite, GUIWidget and by extension GUIObject
org.anotherearth.view.Panel = function(panelBodyId, panelHeaderId, panelId, panelTitle, parentElement, isDraggable, isShrinkable, isMortal) {
	//private attributes
	var panelBody, panel, iterator, iframe;
	var panelObjects = new org.anotherearth.util.ArrayList();
	var panelBodyId = panelBodyId;
	var panelHeaderId = panelHeaderId;
	var panelId = panelId;
	var panelTitle = panelTitle;
	var parentElement = parentElement;
	var isDraggable = isDraggable;
	var isShrinkable = isShrinkable;
	var isMortal = isMortal;
	var tabIndex = 1;
	var self = this;
	
	//private methods
	var _setDraggableContainment = function(containment) {
		$(panel).draggable('option', 'containment', containment);
	};

	var _createDragHandle = function() {
		var panelDragHandle = document.createElement('div');
		$(panelDragHandle).addClass(org.anotherearth.CP_CAPTION_BUTTON_CLASS).addClass('drag_handle').addClass('ui-state-default');
		var panelDragHandleSpan = document.createElement('span');
		$(panelDragHandleSpan).addClass('ui-icon').addClass('ui-icon-arrow-4-diag');
		panelDragHandle.appendChild(panelDragHandleSpan);
		$(panelDragHandle).bind('mouseleave mouseenter', function() {
			$(this).toggleClass('ui-state-hover');
		});
		$(panelDragHandle).bind('mousedown', function() {
			var panelOffset       = $(panel).offset();//the sum of these offsets can potentially change
			var dragHandleOffset  = $(panelDragHandle).offset();  
			var widthContainment  = $(window).width()   + panelOffset.left - dragHandleOffset.left - $(panelDragHandle).width()  - 10;
			var heightContainment = $(window).height()  + panelOffset.top  - dragHandleOffset.top  - $(panelDragHandle).height() - 10;
			//setting confinement here works, whereas setting it with draggable.start() does not
		  _setDraggableContainment([0, 0, widthContainment, heightContainment] );
		});
		$(panelDragHandle).bind('focus blur', function() {
			$(this).toggleClass('ui-state-focus');
		});
		$(panel).draggable({containment: 'window',//should never use this, as containment set on mouse down, but seems that occasionally it is necessary
		                    handle: panelDragHandle,
												scroll: false,
		                    start:  function() {
	                      	self.createIterator();              //out of the window by expansion of the panel - in this case, though, does
		                    	while (iterator.hasNext()) {        //increase the size of the document beyond the viewport
		                    		var next = iterator.next();       //TODO try using chain of command to capture event fired by child to disable confinement temporarily, during expansion    
		                    		if (next instanceof org.anotherearth.view.SelectBox) {
															//workaround for somewhat flawed plugin
		                    			next.hideDropDownList();
		                    		}
		                    	}
		                    	$(panelDragHandle).addClass('ui-state-active');
		                    },
		                    stop: function() {
		                   		$(panelDragHandle).removeClass('ui-state-active');
		                   	}
		                   });
		return panelDragHandle;
	};

	var _createShrinkingButton = function() {//TODO: refactor to eliminate repeated code in these caption buttons - compose with SimpleButton
		var shrinkingIcon = document.createElement('div');
		$(shrinkingIcon).addClass('ui-state-default').addClass(org.anotherearth.CP_CAPTION_BUTTON_CLASS);
		var shrinkingIconSpan = document.createElement('span');
		shrinkingIcon.appendChild(shrinkingIconSpan);
		$(shrinkingIconSpan).addClass('ui-icon').addClass(org.anotherearth.CP_OPEN_ICON_CLASS);
		$(shrinkingIcon).click(function() {
			self.createIterator();
			if ($(shrinkingIconSpan).hasClass(org.anotherearth.CP_SHUT_ICON_CLASS)) {
				while (iterator.hasNext()) {
					iterator.next().show();
				}
			}
			if (!$.support.leadingWhitespace) {//if is IE - else dropdown button icons are misaligned
				$(panelBody).show();
				}
			else {
				$(panelBody).slideToggle(175);
			}
			//Necessary to obtain size before closing in order to prevent shrinking caused by width: auto.
			if ($(shrinkingIconSpan).hasClass(org.anotherearth.CP_OPEN_ICON_CLASS)) {
				while (iterator.hasNext()) {
					iterator.next().hide();
				}
			}
			$(shrinkingIconSpan).toggleClass(org.anotherearth.CP_SHUT_ICON_CLASS).toggleClass(org.anotherearth.CP_OPEN_ICON_CLASS);
			return false;//else page reloads - suppressing default button action
		}).bind('mouseleave', function() {
			$(this).removeClass('ui-state-active');
		}).bind('mouseleave mouseenter', function() {
			$(this).toggleClass('ui-state-hover');
		}).bind('mousedown mouseup', function() {
			$(this).toggleClass('ui-state-active');
		}).bind('focus blur', function() {
			$(this).toggleClass('ui-state-focus');
		});
		return shrinkingIcon;
	};

	var _createKillingButton = function() {
		var killingButton = document.createElement('div');
		$(killingButton).addClass('ui-state-default').addClass(org.anotherearth.CP_CAPTION_BUTTON_CLASS);
		var killingButtonSpan = document.createElement('span');
		killingButton.appendChild(killingButtonSpan);
		$(killingButtonSpan).addClass('ui-icon').addClass('ui-icon-close');
		$(killingButton).click(function() {
			$(panel).remove();
			return false;//else page reloads - suppressing default button action
		}).bind('mouseleave', function() {
			$(this).removeClass('ui-state-active');
		}).bind('mouseleave mouseenter', function() {
			$(this).toggleClass('ui-state-hover');
		}).bind('mousedown mouseup', function() {
			$(this).toggleClass('ui-state-active');
		}).bind('focus blur', function() {
			$(this).toggleClass('ui-state-focus');
		});
		return killingButton;
	};

	//inner class
	var _PanelIterator = function(iterator) {
		//constructor
		//org.anotherearth.util.Interface.ensureImplements(iterator, org.anotherearth.Iterator);
		var iteratorArray = [];
		iteratorArray.push(iterator);

		//privileged methods
		this.next = function() {
			if (this.hasNext()) {
				var iterator = iteratorArray[iteratorArray.length-1];
				var component = iterator.next();
				if (/*component instanceof org.anotherearth.view.ControlPanelFieldSet ||*/
						component instanceof org.anotherearth.view.ShrinkableSubPanel) {
					iteratorArray.push(component.createIterator());	
				}
				return component;
			}
			else {
				return null;
			}
		};

		this.hasNext = function() {
			if (iteratorArray.length === 0) {
				return false;
			}
			else {
				var iterator = iteratorArray[iteratorArray.length-1];
				if (!iterator.hasNext()) {
					iteratorArray.pop();
					return this.hasNext();
				}
				else {
					return true;
				}
			}
		};
	};	

	//privileged methods
	this.addChild = function(panelObject) {
		//org.anotherearth.util.Interface.ensureImplements(panelObject, org.anotherearth.GUIComposite, org.anotherearth.GUIObject);
		panelObjects.add(panelObject);
		panelBody.appendChild(panelObject.getContainingElement());
	};
	this.closeSubPanels = function() {
		this.createIterator();
		while (iterator.hasNext()) {
			var next = iterator.next();
			if (next instanceof org.anotherearth.view.ShrinkableSubPanel) {
				next.close();
			}
		}
	};
	this.createGUIElements = function(panelBodyId, panelHeaderId, panelId, panelTitle, parentElement) {
		panel = document.createElement('form');//form solely to allow tab access
		panel.id = panelId;
		panel.setAttribute("z-index", "10");
		$(panel).addClass('panel').addClass('ui-widget').addClass('ui-widget-content');

		var panelHeader = document.createElement('div');
		panelHeader.id = panelHeaderId;
		$(panelHeader).addClass('panel_header');

		var panelTitleElement = document.createElement('h4');
		panelTitleElement.appendChild(document.createTextNode(panelTitle));
		$(panelTitleElement).addClass(org.anotherearth.PANEL_TITLE_CLASS);

		panelBody = document.createElement('div');
		panelBody.id = panelBodyId;

		if (isMortal) {
			panelHeader.appendChild(_createKillingButton());
		}
		if (isShrinkable) {
			panelHeader.appendChild(_createShrinkingButton());
		}
		if (isDraggable) {
			panelHeader.appendChild(_createDragHandle());
		}
		panelHeader.appendChild(panelTitleElement);
		panel.appendChild(panelHeader);
		panel.appendChild(panelBody);

		panel.style.display = 'none';
		
		iframe = org.anotherearth.util.IFrameGenerator.createFrame();
		panel.insertBefore(iframe, panel.firstChild);
		
		$(panel).bgiframe();

		parentElement.appendChild(panel);
	};
		
	this.getContainingElement = function() {
		return panel;
	};
	this.getIterator = function() {
		if (typeof iterator !== undefined) {
			return iterator;
		}
	};
	this.performNewEarthPropsUpdate = function() {
		this.createIterator();
		while (iterator.hasNext()) {
			iterator.next().performNewEarthPropsUpdate();
		}
	};
	this.performUndoRedoUpdate = function() {
		this.createIterator();
		while (iterator.hasNext()) {
			iterator.next().performUndoRedoUpdate();
		}
	};
	this.removeChild = function(panelObject) {
		panelObjects.remove(panelObjects.getIndexOf(panelObject));
		this.setTabIndex(2);
	};
	this.show = function() {
		this.createIterator();
		while (iterator.hasNext()) {
			iterator.next().show();
		}
		//this.setTabIndex(tabIndex);
		panel.style.display = 'block';
	};
	this.hide = function() {
		this.createIterator();
		while (iterator.hasNext()) {
			iterator.next().hide();
		}
		panel.style.display = 'none';
	};
	this.setTabIndex = function(initialTabIndex) {
		var tabIndex = initialTabIndex;
		this.createIterator();
		while (iterator.hasNext()) {
			tabIndex = iterator.next().setTabIndex(tabIndex);
		}
	};
	this.createIterator = function() {
		iterator = new _PanelIterator(panelObjects.iterator());//TODO: don't like creating a new one each time
	};

	//constructor
	this.createGUIElements(panelBodyId, panelHeaderId, panelId, panelTitle, parentElement);
};

//implements TwoEarthsObserver, GUIComposite, GUIWidget and by extension GUIObject
org.anotherearth.view.ControlPanel = function(panelWidgetsContainerId, panelHeaderId, panelId, panelTitle, parentElement, isDraggable, isShrinkable, isMortal) {
	//private attributes
	var panel;

	//privileged methods
	this.addChild = function(controlPanelObject) {
		//org.anotherearth.util.Interface.ensureImplements(controlPanelObject, org.anotherearth.TwoEarthsObserver);
		panel.addChild(controlPanelObject);
	};
	this.closeSubPanels = function() {
		panel.closeSubPanels();
	};
	this.createGUIElements = function(panelWidgetsContainerId, panelHeaderId, panelId, panelTitle, parentElement) {
		panel.createGUIElements(panelWidgetsContainerId, panelHeaderId, panelId, panelTitle, parentElement);
	};
	this.getContainingElement = function() {
		return panel.getContainingElement();
	};
	this.performNewEarthPropsUpdate = function() {
		this.createIterator();
		var iterator = panel.getIterator();
		while (iterator.hasNext()) {
			iterator.next().performNewEarthPropsUpdate();
		}
	};
	this.performUndoRedoUpdate = function() {
		this.createIterator();
		var iterator = panel.getIterator();
		while (iterator.hasNext()) {
			iterator.next().performUndoRedoUpdate();
		}
	};
	this.removeChild = function(panelObject) {
		panel.removeChild(panelObject);
	};
	this.show = function() {
		panel.show();
	};
	this.hide = function() {
		panel.hide();
	};
	this.setTabIndex = function(initialTabIndex) {//TODO: should/could tab index be set with visitor pattern
		panel.setTabIndex(initialTabIndex);
	};
	this.createIterator = function() {
		panel.createIterator();
	};

	//constructor
	panel = new org.anotherearth.view.Panel(panelWidgetsContainerId, panelHeaderId, panelId, panelTitle, parentElement, isDraggable, isShrinkable, isMortal);
};
