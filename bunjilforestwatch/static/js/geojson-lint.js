/*
 * Base on CodeMirror, copyright (c) by Marijn Haverbeke and others 
 * Distributed under an MIT license: http://codemirror.net/LICENSE

 * Depends on jsonlint.js     from https://github.com/zaach/jsonlint
 * Depends on geojsonhint.hs  from https://github.com/mapbox/geojsonhint
 */

/* global jsonlint */
/* global geojsonhint */
/* global CodeMirror */
/* global initialize_map */

(function(mod) {
	"use strict";

	if (typeof exports === "object" && typeof module === "object") {// CommonJS
    mod(require("../../lib/codemirror"));
  }  
  else if (typeof define === "function" && define.amd) {// AMD
    define(["../../lib/codemirror"], mod);
  }  
  else {// Plain browser env
	  mod(CodeMirror);
  }  
})(function(CodeMirror) {
"use strict";

CodeMirror.registerHelper("lint", "json", function(text) {
  var found = [];
  
  jsonlint.parseError = function(str, hash) {
	    var loc = hash.loc;
	    found.push({title: 'Invalid JSON', 
	    			from: CodeMirror.Pos(loc.first_line - 1, loc.first_column),
	                to: CodeMirror.Pos(loc.last_line - 1, loc.last_column),
	                message: str});
	  };
	  
  
  if(text!== "") {
	  var editor = this;
	  geojson_validate(editor, text, found);
  }
  return found;
});

function geojson_validate(editor, text, found) { /* not used */

    function handleError(msg) {
        var match = msg.match(/line (\d+)/);
        if (match && match[1]) {
            found.push({
            	title: 'Invalid GeoJson', 
    			from: CodeMirror.Pos(parseInt(match[1], 10) - 1, 1 ),
                to:   CodeMirror.Pos(parseInt(match[1], 10) - 1, 1),
                message: msg.message});
       }
     }

    function handleErrors(errors) {
        errors.forEach(function(e) {
            found.push({
            	title: 'Invalid GeoJson', 
    			from: CodeMirror.Pos(e.line, 1),
                to:   CodeMirror.Pos(e.line, 1),
                message: e.message});
        });
    }

    var err = geojsonhint.hint(text);
 
    if (err instanceof Error) {
        handleError(err.message);
        
    } else if (err.length) {
        handleErrors(err);
        
    } else {
    	
    }

}




});
