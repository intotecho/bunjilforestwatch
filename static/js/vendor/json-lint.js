// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE

// Depends on jsonlint.js from https://github.com/zaach/jsonlint

// declare global: jsonlint

(function(mod) {
  if (typeof exports == "object" && typeof module == "object") // CommonJS
    mod(require("../../lib/codemirror"));
  else if (typeof define == "function" && define.amd) // AMD
    define(["../../lib/codemirror"], mod);
  else // Plain browser env
    mod(CodeMirror);
})(function(CodeMirror) {
"use strict";

CodeMirror.registerHelper("lint", "json", function(text) {
  var found = [];
  jsonlint.parseError = function(str, hash) {
    var loc = hash.loc;
    found.push({from: CodeMirror.Pos(loc.first_line - 1, loc.first_column),
                to: CodeMirror.Pos(loc.last_line - 1, loc.last_column),
                message: str});
  };
  try { jsonlint.parse(text); }
  catch(e) {}
  return found;
});

function geojson_validate(editor, changeObj) { /* not used */
	'use strict';
	
	/* global geojsonhint */
    var err = geojsonhint.hint(editor.getValue());
    editor.clearGutter('error');

    if (err instanceof Error) {
        handleError(err.message);
        return callback({
            'class': 'icon-circle-blank',
            title: 'invalid JSON',
            message: 'invalid JSON'});
    } else if (err.length) {
        handleErrors(err);
        /*
        return callback({
            'class': 'icon-circle-blank',
            title: 'invalid GeoJSON',
            message: 'invalid GeoJSON'});
            */
    } else {
        var zoom = changeObj[0].from.ch === 0 &&
            changeObj[0].from.line === 0 &&
            changeObj[0].origin === 'paste';

        var gj = JSON.parse(editor.getValue());
        /*
        try {
            return callback(null, gj, zoom);
        } catch(e) {
            return callback({
                'class': 'icon-circle-blank',
                title: 'invalid GeoJSON',
                message: 'invalid GeoJSON'});
        }
        */
    }

    function handleError(msg) {
        var match = msg.match(/line (\d+)/);
        if (match && match[1]) {
            editor.clearGutter('error');
            editor.setGutterMarker(parseInt(match[1], 10) - 1, 'error', makeMarker(msg));
        }
    }

    function handleErrors(errors) {
        editor.clearGutter('error');
        errors.forEach(function(e) {
            editor.setGutterMarker(e.line, 'error', makeMarker(e.message));
        });
    }

    function makeMarker(msg) {
        return d3.select(document.createElement('div'))
            .attr('class', 'error-marker')
            .attr('message', msg).node();
    }
}




});
