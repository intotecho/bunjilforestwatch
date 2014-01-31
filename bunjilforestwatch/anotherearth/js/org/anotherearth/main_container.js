//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};

org.anotherearth.Container = (function() { //singleton with deferred instantiation.  Dependency injector - primarily to facilitate unit testing.
	var uniqueInstance;

	function constructor() {
		var coms = {}; //coms = components
		var ae 	 = org.anotherearth;
		var body = $('body')[0];

		var urlManager = ae.model.URLManager;
		var initialLCameraProps = {};
		var initialRCameraProps = {};
		var initialLocks = {};
		var queryStringValues = {};
		queryStringValues.latLng  = urlManager.getURLQueryStringValue('isLatLngLocked');
		queryStringValues.alt     = urlManager.getURLQueryStringValue('isAltLocked');
		queryStringValues.tilt    = urlManager.getURLQueryStringValue('isTiltLocked');
		queryStringValues.heading = urlManager.getURLQueryStringValue('isHeadingLocked'); 
		for (var value in queryStringValues) {
			initialLocks[value] = ((queryStringValues[value] !== null) ? parseInt(queryStringValues[value], 10) : 1);
		}
		initialLCameraProps.lat  = parseFloat(urlManager.getURLQueryStringValue('LLat'))  || ae.DEFAULT_L_EARTH_COORDS.LAT;
		initialLCameraProps.lng  = parseFloat(urlManager.getURLQueryStringValue('LLng'))  || ae.DEFAULT_L_EARTH_COORDS.LNG;
		initialLCameraProps.alt  = parseFloat(urlManager.getURLQueryStringValue('LAlt'))  || ae.DEFAULT_L_EARTH_COORDS.ALT;
		initialLCameraProps.tilt = parseFloat(urlManager.getURLQueryStringValue('LTilt')) || ae.DEFAULT_L_EARTH_COORDS.TILT;
		initialLCameraProps.head = parseFloat(urlManager.getURLQueryStringValue('LHead')) || ae.DEFAULT_L_EARTH_COORDS.HEAD;
		initialLCameraProps.date = urlManager.getURLQueryStringValue('LDate')             || null;
		
		initialRCameraProps.lat  = parseFloat(urlManager.getURLQueryStringValue('RLat'))  || ae.DEFAULT_R_EARTH_COORDS.LAT;
		initialRCameraProps.lng  = parseFloat(urlManager.getURLQueryStringValue('RLng'))  || ae.DEFAULT_R_EARTH_COORDS.LNG;
		initialRCameraProps.alt  = parseFloat(urlManager.getURLQueryStringValue('RAlt'))  || ae.DEFAULT_R_EARTH_COORDS.ALT;
		initialRCameraProps.tilt = parseFloat(urlManager.getURLQueryStringValue('RTilt')) || ae.DEFAULT_R_EARTH_COORDS.TILT;
		initialRCameraProps.head = parseFloat(urlManager.getURLQueryStringValue('RHead')) || ae.DEFAULT_R_EARTH_COORDS.HEAD;
		initialRCameraProps.date = urlManager.getURLQueryStringValue('RDate')             || null;

		coms.welcomePanel = new ae.view.Panel(ae.WELCOME_PANEL_BODY_ID,
		                                      ae.WELCOME_PANEL_HEADER_ID,
									          ae.WELCOME_PANEL_ID,
											  'Welcome to anotherearth.org',
											  body,
											  true,
											  true,
											  true);
		var welcomeText = document.createElement('div');
		welcomeText.innerHTML = '<p>This application allows you to compare two maps easily and comprehensively, ' +
		                        'using the Google Earth browser plugin. ' +
					'An example use would be comparing two maps of the same place at different times; ' +
		                        'noteworthy comparisons can be saved as URL links. ' +
		                        'In addition, movement of the Earths can be synchronized, movements undone and redone, and features such as buildings, roads and borders added.</p>' +
								            //'<p>Please see the <a href="Pakistan_floods/index.html">sub-site dedicated to the recent flooding in Pakistan</a>.</p>' +
		                        '<p>Please refer to Google\'s documentation ' +
		                        'for guides to Google Earth and its navigation control.</p>' +
		                        '<p>If your browser\'s preferred language isn\'t English then using a ' +
		                        'translator, <span id=\"google_branding\"></span>, ' +
		                        'I\'ve attempted to convert the text.</p>' +
		                        '<p>I hope you find the application useful! Please feel free to contact me at <a href="mailto:contact@anotherearth.org">contact@anotherearth.org</a>.</p>';
		
		if (!$.support.leadingWhitespace) {//if is IE
			welcomeText.innerHTML += '<p id="IE_message">Sorry, but to ensure an optimal experience with this site, I recommend using the ' +
			                         '<a href="http://www.mozilla.com">Mozilla Firefox</a> or <a href="http://www.google.com/chrome">Google Chrome</a> web browsers.</p>';
		}

		coms.welcomePanel.addChild(new ae.view.MiscellaneousElement(welcomeText));
		google.language.getBranding('google_branding');
		
		//main MVC objects
		coms.earthsManager    = new ae.model.EarthsManager();
		coms.earthsController = new ae.controller.EarthsController(coms.earthsManager, urlManager); 
		coms.leftEarth	      = new ae.view.LockableEarth(ae.L_EARTH_ID, coms.earthsController, initialLCameraProps);
		coms.rightEarth       = new ae.view.LockableEarth(ae.R_EARTH_ID, coms.earthsController, initialRCameraProps);
		coms.controlPanel     = new ae.view.ControlPanel(ae.CP_BUTTONS_CONTAINER_ID,//TODO: consider using builder pattern
														 ae.CP_HEADER_ID,
														 ae.CP_ID,
														 'Control Panel',
														 body,
														 true,
														 true,
														 false);
		coms.earthsController.setLeftEarth(coms.leftEarth);
		coms.earthsController.setRightEarth(coms.rightEarth);
		coms.earthsController.setControlPanel(coms.controlPanel);
		coms.earthsManager.registerNewEarthObserver(coms.controlPanel);
		coms.earthsManager.registerUndoRedoObserver(coms.controlPanel);
		coms.earthsManager.registerUndoRedoObserver(coms.earthsController);

		/*comand objects*/
			//locking checkboxes
		coms.linkCreatorCommand                  = new ae.command.LinkCreatorCommand(coms.earthsController);
		coms.toggleVerticalMovementLockCommand 	 = new ae.command.ToggleMovementLockCommand('vertical', coms.earthsController);
		coms.toggleHorizontalMovementLockCommand = new ae.command.ToggleMovementLockCommand('horizontal', coms.earthsController);
		coms.toggleTiltLockCommand               = new ae.command.ToggleMovementLockCommand('tilt', coms.earthsController);
		coms.toggleHeadingLockCommand            = new ae.command.ToggleMovementLockCommand('head', coms.earthsController);
		
			//buttons
		coms.undoCommand                  = new ae.command.UndoCommand(coms.earthsController);
		coms.redoCommand                  = new ae.command.RedoCommand(coms.earthsController);
		coms.equateCameraAltitudesCommand = new ae.command.EquateCameraAltitudesCommand(coms.earthsController);
		coms.equateCameraLatsLngsCommand  = new ae.command.EquateCameraLatsLngsCommand(coms.earthsController);
		coms.equateCameraTiltsCommand     = new ae.command.EquateCameraTiltsCommand(coms.earthsController);
		coms.equateCameraHeadingsCommand  = new ae.command.EquateCameraHeadingsCommand(coms.earthsController);
			//select box
		coms.toggleEarthExtraCommand      = new ae.command.ToggleEarthExtraCommand(coms.earthsController);
			//radio buttons
		coms.toggleDonorEarthCommand      = new ae.command.ToggleDonorEarthCommand(coms.earthsController);

		//strategy objects
		coms.linkCreatingButtonUpdateStrategy = new ae.view.LinkCreatingButtonUpdateStrategy();
		coms.undoButtonUpdateStrategy         = new ae.view.UndoButtonUpdateStrategy();
		coms.redoButtonUpdateStrategy         = new ae.view.RedoButtonUpdateStrategy();
		coms.equateCameraLatsLngsStrategy     = new ae.view.EquateLatLngsButtonStrategy();
		coms.equateCameraAltitudesStrategy    = new ae.view.EquateAltitudesButtonStrategy();
		coms.equateCameraTiltsStrategy        = new ae.view.EquateTiltsButtonStrategy();
		coms.equateCameraHeadingsStrategy     = new ae.view.EquateHeadingsButtonStrategy();
		
		//gui objects
			//checkboxes
		coms.altLockingCheckbox     = new ae.view.TwoEarthsCheckbox("altitudes",
																	ae.CP_ALTITUDE_LOCK_CHECKBOX_ID,
																	coms.earthsManager);
		coms.latLngLockingCheckbox  = new ae.view.TwoEarthsCheckbox("latitudes and longitudes",
																	ae.CP_VIEW_CENTER_LOCK_CHECKBOX_ID,
																	coms.earthsManager);
		coms.tiltLockingCheckbox    = new ae.view.TwoEarthsCheckbox("tilts",
																	ae.CP_TILT_LOCK_CHECKBOX_ID,
																	coms.earthsManager);
		coms.headingLockingCheckbox = new ae.view.TwoEarthsCheckbox("headings",
																	ae.CP_HEAD_LOCK_CHECKBOX_ID,
																	coms.earthsManager);

		coms.altLockingCheckbox.addClickEventListener(coms.toggleVerticalMovementLockCommand);
		coms.latLngLockingCheckbox.addClickEventListener(coms.toggleHorizontalMovementLockCommand);
		coms.tiltLockingCheckbox.addClickEventListener(coms.toggleTiltLockCommand);
		coms.headingLockingCheckbox.addClickEventListener(coms.toggleHeadingLockCommand);

		//buttons
		coms.undoButton = new ae.view.TwoEarthsButton('undo spatial change', ae.CP_UNDO_BUTTON_ID, coms.earthsManager);
		coms.undoButton.addClickEventListener(coms.undoCommand);
		coms.undoButton.setUndoRedoUpdateStrategy(coms.undoButtonUpdateStrategy);
		coms.undoButton.setNewEarthPropsUpdateStrategy(coms.undoButtonUpdateStrategy);
		coms.undoButton.setIsEnabled(false);

		coms.redoButton = new ae.view.TwoEarthsButton('redo spatial change', ae.CP_REDO_BUTTON_ID, coms.earthsManager);
		coms.redoButton.addClickEventListener(coms.redoCommand);
		coms.redoButton.setUndoRedoUpdateStrategy(coms.redoButtonUpdateStrategy);
		coms.redoButton.setNewEarthPropsUpdateStrategy(coms.redoButtonUpdateStrategy);
		coms.redoButton.setIsEnabled(false);
		
		coms.equateCameraLatsLngsButton = new ae.view.TwoEarthsButton("latitude and longitude",
		                                                              ae.EQUATE_CAM_LATS_LNGS_BUTTON_ID,
		                                                              coms.earthsManager);
		coms.equateCameraLatsLngsButton.addClickEventListener(coms.equateCameraLatsLngsCommand);
		coms.equateCameraLatsLngsButton.setUndoRedoUpdateStrategy(coms.equateCameraLatsLngsStrategy);
		coms.equateCameraLatsLngsButton.setNewEarthPropsUpdateStrategy(coms.equateCameraLatsLngsStrategy);
		
		coms.equateCameraAltitudesButton = new ae.view.TwoEarthsButton('altitude',
		                                                               ae.EQUATE_CAM_ALTITUDES_BUTTON_ID,
		                                                               coms.earthsManager);
		coms.equateCameraAltitudesButton.addClickEventListener(coms.equateCameraAltitudesCommand);
		coms.equateCameraAltitudesButton.setUndoRedoUpdateStrategy(coms.equateCameraAltitudesStrategy);
		coms.equateCameraAltitudesButton.setNewEarthPropsUpdateStrategy(coms.equateCameraAltitudesStrategy);

		coms.equateCameraTiltsButton = new ae.view.TwoEarthsButton('tilt',
		                                                           ae.EQUATE_CAM_TILTS_BUTTON_ID,
		                                                           coms.earthsManager);
		coms.equateCameraTiltsButton.addClickEventListener(coms.equateCameraTiltsCommand);
		coms.equateCameraTiltsButton.setUndoRedoUpdateStrategy(coms.equateCameraTiltsStrategy);
		coms.equateCameraTiltsButton.setNewEarthPropsUpdateStrategy(coms.equateCameraTiltsStrategy);
		
		coms.equateCameraHeadingsButton = new ae.view.TwoEarthsButton('heading',
		                                                              ae.EQUATE_CAM_HEADINGS_BUTTON_ID,
		                                                              coms.earthsManager);
		coms.equateCameraHeadingsButton.addClickEventListener(coms.equateCameraHeadingsCommand);
		coms.equateCameraHeadingsButton.setUndoRedoUpdateStrategy(coms.equateCameraHeadingsStrategy);
		coms.equateCameraHeadingsButton.setNewEarthPropsUpdateStrategy(coms.equateCameraHeadingsStrategy);

		coms.linkCreatorButton = new ae.view.LinkCreatorButton("create link",
		                                                       ae.CP_LINK_CREATOR_BUTTON_ID,
		                                                       ae.CP_LINK_BOX_ID,
		                                                       coms.earthsManager);
		coms.linkCreatorButton.setUndoRedoUpdateStrategy(coms.linkCreatingButtonUpdateStrategy);
		coms.linkCreatorButton.setNewEarthPropsUpdateStrategy(coms.linkCreatingButtonUpdateStrategy);
		coms.linkCreatorButton.setIsEnabled(true);
		coms.linkCreatorButton.addClickEventListener(coms.linkCreatorCommand);
		coms.earthsController.setLinkCreatorButton(coms.linkCreatorButton);

		//radio buttons
		var donorRadios = [];
		var leftCameraRadios   = {};
		var rightCameraRadios  = {};
		leftCameraRadios.id    = 'pick_left_camera';
		leftCameraRadios.value = 'left_earth';
		leftCameraRadios.name  = 'donor_camera_selector';
		leftCameraRadios.label = 'from left camera';
		donorRadios.push(leftCameraRadios);
		rightCameraRadios.id    = 'pick_right_camera';
		rightCameraRadios.value = 'right_earth';
		rightCameraRadios.name  = 'donor_camera_selector'; 
		rightCameraRadios.label = 'from right camera';
		donorRadios.push(rightCameraRadios);
		coms.donorRadioButtons = new ae.view.RadioButtons(donorRadios, 'donor_camera_selector');
		coms.donorRadioButtons.addClickEventListener(coms.toggleDonorEarthCommand);

		//select box
		var borderOption          = {};
		var hiResBuildingsOption  = {};	
		var loResBuildingsOption  = {};
		var roadsOption           = {};
		var terrainOption         = {};
		var sunOption             = {};
		var atmosphereOption      = {};
		var timeOption            = {};
		var latLngGridlinesOption = {};
		
		//FIXME options should be an enum equivalent within LockableEarth
        //TODO make scale bars and status bar selectable
		borderOption.text  = "borders and towns";
		borderOption.value = "borders";
		hiResBuildingsOption.text  = "hi-res buildings";
		hiResBuildingsOption.value = "hiRes";
		loResBuildingsOption.text  = "lo-res buildings";
		loResBuildingsOption.value = "loRes";
		roadsOption.text  = "roads";
		roadsOption.value = "roads";
		terrainOption.text  = "terrain";
		terrainOption.value = "terrain";
		sunOption.text  = "sun";
		sunOption.value = "sun";
		atmosphereOption.text  = "atmosphere";
		atmosphereOption.value = "atmosphere";
		latLngGridlinesOption.text  = "grid";
		latLngGridlinesOption.value = "grid";
		timeOption.text  = "time control";
		timeOption.value = "time";
		var LEarthOptions = [borderOption,
		                     hiResBuildingsOption,
		                     loResBuildingsOption,
		                     latLngGridlinesOption,
		                     roadsOption,
		                     sunOption,
		                     terrainOption,
		                     timeOption
		                     //atmosphereOption//TODO: no one's going to be turning this off, most likely
		                     ];
		var REarthOptions = [$.extend(true, {}, borderOption),           //deep copies of the option objects
		                     $.extend(true, {}, hiResBuildingsOption),
                             $.extend(true, {}, loResBuildingsOption),
		                     $.extend(true, {}, latLngGridlinesOption),
		                     $.extend(true, {}, roadsOption),
                             $.extend(true, {}, sunOption),
		                     $.extend(true, {}, terrainOption),
                             $.extend(true, {}, timeOption)
		                     //$.extend(true, {}, atmosphereOption)
                             ];
		
		coms.LEarthOptionSelector = new ae.view.SelectBox(LEarthOptions,
		                                                  1,
		                                                  'left Earth',
		                                                  ae.CP_L_EARTH_EXTRAS_SELECTOR_ID,
		                                                  true);
		coms.REarthOptionSelector = new ae.view.SelectBox(REarthOptions,
		                                                  1,
		                                                  'right Earth',
		                                                  ae.CP_R_EARTH_EXTRAS_SELECTOR_ID,
		                                                  true);

		coms.LEarthOptionSelector.addClickEventListener(coms.toggleEarthExtraCommand);
		coms.REarthOptionSelector.addClickEventListener(coms.toggleEarthExtraCommand);
		
		//search boxes
		coms.leftEarthSearch  = new ae.view.SearchBox(coms.leftEarth,  coms.earthsController, ae.L_EARTH_SEARCH_BOX_ID, 'left Earth');
		coms.rightEarthSearch = new ae.view.SearchBox(coms.rightEarth, coms.earthsController, ae.R_EARTH_SEARCH_BOX_ID, 'right Earth');

		//control panel fieldsets
		coms.checkBoxSubPanel           = new ae.view.ShrinkableSubPanel("synchronize camera movement",
		                                                                 ae.CP_CAMERA_PROPERTY_LOCKING_SUB_PANEL_ID);	
		coms.cameraPropCopyingSubPanel  = new ae.view.ShrinkableSubPanel("copy camera coordinates",
		                                                                 ae.CP_CAMERA_PROPERTY_COPYING_SUB_PANEL_ID);	
		coms.earthOptionsSubPanel       = new ae.view.ShrinkableSubPanel("Earth extras",
		                                                                 ae.CP_EARTH_OPTIONS_SUB_PANEL_ID);	
		coms.searchBoxSubPanel          = new ae.view.ShrinkableSubPanel("search",
		                                                                 ae.CP_SEARCH_BOX_SUB_PANEL_ID);	
		var googleBranding = document.createElement('span');
		googleBranding.id = 'google_search_branding';

		$(coms.searchBoxSubPanel.getContainingElement()).find('.sub_panel_title').append(googleBranding);

		coms.miscellanySubPanel         = new ae.view.ShrinkableSubPanel("undo/redo and URL link",
		                                                                 ae.CP_MISC_OPTIONS_SUB_PANEL_ID);			

		
		/* callbacks on earths and one earth's kml, loading */ 
		var getLoadedEarths = (function() {
			var loadedEarths = 0;
			return function() { return ++loadedEarths; };
		})();

		var responseToEarthFullyLoading = function() {
			if (getLoadedEarths() === 2) {
				coms.LEarthOptionSelector.setIsSelected(coms.LEarthOptionSelector.getIndexOfOption("time"), true);
				coms.REarthOptionSelector.setIsSelected(coms.REarthOptionSelector.getIndexOfOption("time"), true);
				coms.altLockingCheckbox.setIsChecked(initialLocks.alt);
				coms.tiltLockingCheckbox.setIsChecked(initialLocks.tilt);
				coms.latLngLockingCheckbox.setIsChecked(initialLocks.latLng);
				coms.headingLockingCheckbox.setIsChecked(initialLocks.heading);
				coms.donorRadioButtons.setIsChecked(true, coms.donorRadioButtons.getIndexOf('left_camera'));
				coms.controlPanel.performNewEarthPropsUpdate();
				coms.controlPanel.show();
				//need to set these widths in pixels once the elements have been created to avoid jerkiness and resizing with subpanel and panel shrinking (jQuery flaws)
				$('#' + ae.CP_ID + ' button').width($('#' + ae.CP_ID + ' button').width());
				$('#' + ae.CP_ID).width($('#' + ae.CP_ID).width());
				var viewportHeight = window.innerHeight ? window.innerHeight : $(window).height();
				var controlPanelElement = coms.controlPanel.getContainingElement();
				var panelTopOffset = parseInt(($(controlPanelElement).css('top')).replace(/(\d+)px/, "$1"), 10);
				if (viewportHeight <= (($(coms.controlPanel.getContainingElement()).outerHeight()) + panelTopOffset)) {
					coms.controlPanel.closeSubPanels();
				}
			}
		};

		coms.earthsController.setEarthLoadingResponseCallback(responseToEarthFullyLoading);

		//add gui widgets to control panel
		coms.checkBoxSubPanel.addChild(coms.altLockingCheckbox);
		coms.checkBoxSubPanel.addChild(coms.headingLockingCheckbox);
		coms.checkBoxSubPanel.addChild(coms.latLngLockingCheckbox);
		coms.checkBoxSubPanel.addChild(coms.tiltLockingCheckbox);
		coms.cameraPropCopyingSubPanel.addChild(coms.donorRadioButtons);
		coms.cameraPropCopyingSubPanel.addChild(coms.equateCameraAltitudesButton);
		coms.cameraPropCopyingSubPanel.addChild(coms.equateCameraHeadingsButton);
		coms.cameraPropCopyingSubPanel.addChild(coms.equateCameraLatsLngsButton);
		coms.cameraPropCopyingSubPanel.addChild(coms.equateCameraTiltsButton);
		coms.earthOptionsSubPanel.addChild(coms.LEarthOptionSelector);
		coms.earthOptionsSubPanel.addChild(coms.REarthOptionSelector);
		coms.miscellanySubPanel.addChild(coms.undoButton);
		coms.miscellanySubPanel.addChild(coms.redoButton);
		coms.miscellanySubPanel.addChild(coms.linkCreatorButton);
		coms.searchBoxSubPanel.addChild(coms.leftEarthSearch);
		coms.searchBoxSubPanel.addChild(coms.rightEarthSearch);
		coms.controlPanel.addChild(coms.earthOptionsSubPanel);
		coms.controlPanel.addChild(coms.searchBoxSubPanel);
		coms.controlPanel.addChild(coms.checkBoxSubPanel);
		coms.controlPanel.addChild(coms.cameraPropCopyingSubPanel);
		coms.controlPanel.addChild(coms.miscellanySubPanel);
		google.language.getBranding('google_search_branding');
		$('.gBrandingText').css('vertical-align', 'text-bottom');

		//PUBLIC METHOD
		return {
			getComponent: function(id) {
				return coms[id];
			}
		};
	}

	return {
		getInstance: function() {
			if (!uniqueInstance) {//Instantiate only if the instance doesn't exist
				uniqueInstance = constructor();
			}
			return uniqueInstance;
		}
	};
})();
