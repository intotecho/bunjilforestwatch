
org = window.org || {};
org.anotherearth = window.org.anotherearth || {};

org.anotherearth.constants = {
	//constants - TODO make immutable
	JAVASCRIPT_DISABLED_MESSAGE_ID:	 'js_disabled_message',
	L_EARTH_ID:                      'left_earth',
	R_EARTH_ID:                      'right_earth',
	L_EARTH_SEARCH_BOX_ID:           'l_earth_search',
	R_EARTH_SEARCH_BOX_ID:           'r_earth_search',
	CP_ID:                           'control_panel',
	CP_HEADER_ID:                    'control_panel_header',
	CP_BUTTONS_CONTAINER_ID:         'control_panel_widgets',
	CP_UNDO_BUTTON_ID:               'undo',
	CP_REDO_BUTTON_ID:               'redo',
	CP_L_EARTH_EXTRAS_SELECTOR_ID:   'left_earth_extras_selector',
	CP_R_EARTH_EXTRAS_SELECTOR_ID:   'right_earth_extras_selector',
	CP_LINK_CREATOR_BUTTON_ID:       'link_creator',
	CP_LINK_BOX_ID:                  'link_box',
	CP_LINK_CREATOR_CONTAINER_ID:    'link_creator_container',
	CP_ALTITUDE_LOCK_CHECKBOX_ID:    'altitude_lock',
	CP_VIEW_CENTER_LOCK_CHECKBOX_ID: 'view_center_lock',
	CP_TILT_LOCK_CHECKBOX_ID:        'tilt_lock',
	CP_HEAD_LOCK_CHECKBOX_ID:        'heading_lock',
	CP_EARTH_OPTIONS_SUB_PANEL_ID:   'earth_options',
	CP_MISC_OPTIONS_SUB_PANEL_ID: 	 'misc_options',
	CP_SEARCH_BOX_SUB_PANEL_ID:      'search_boxes',
	WELCOME_PANEL_ID:                'welcome_panel',
	WELCOME_PANEL_HEADER_ID:         'welcome_panel_header',
	WELCOME_PANEL_BODY_ID:           'welcome_panel_body',
	EQUATE_CAM_ALTITUDES_BUTTON_ID:  'equate_camera_altitudes',
	EQUATE_CAM_LATS_LNGS_BUTTON_ID:  'equate_camera_latitudes_and_longitudes',
	EQUATE_CAM_TILTS_BUTTON_ID:      'equate_camera_tilts',
	CP_CAMERA_PROPERTY_LOCKING_SUB_PANEL_ID: 'camera_propety_locking_checkboxes',
	CP_CAMERA_PROPERTY_COPYING_SUB_PANEL_ID: 'camera_property_copying_buttons',
	EARTH_CANVAS_CLASS:      'earth_canvas',
	CP_OPEN_ICON_CLASS:      'ui-icon-arrowthickstop-1-n',
	CP_SHUT_ICON_CLASS:      'ui-icon-arrowthickstop-1-s',
	CP_CAPTION_BUTTON_CLASS: 'control_panel_caption_button',
	SUB_PANEL_CAPTION_BUTTON_CLASS: 'sub_panel_caption_button',
	SUB_PANEL_SHUT_ICON_CLASS: 'ui-icon-circle-triangle-e',
	SUB_PANEL_OPEN_ICON_CLASS: 'ui-icon-circle-triangle-s',
	PANEL_TITLE_CLASS:       'panel_title',
	SEARCH_BOX_CLASS:        'search_box',
	PLUGIN_INCOMPATIBILITY_MESSAGE_ID:  'plugin_incompatibility_message',
	JS_INCOMPATIBILITY_MESSAGE_ID:      'js_incompatibility_message',
	PLAIN_HTML_MESSAGE_ID:              'html_welcome_message',
	DEFAULT_L_EARTH_COORDS: {
		LAT: 33.43,
		LNG: 61.24,
		ALT: 10400000,
		TILT: 0,
		HEAD: 0
	},
	DEFAULT_R_EARTH_COORDS: {
		LAT: 9.61,
		LNG: -78.33,
		ALT: 10400000,
		TILT: 0,
		HEAD: 0
	}		
};

for (constant in org.anotherearth.constants) {
	org.anotherearth[constant] = org.anotherearth.constants[constant];
}

delete org.anotherearth.constants;
