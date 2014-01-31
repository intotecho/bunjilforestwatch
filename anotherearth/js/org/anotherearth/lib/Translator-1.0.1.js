//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.lib = window.org.anotherearth.lib || {};

/**
 * Translator
 * Copyright (c) 2008 Ariel Flesler - aflesler(at)gmail(dot)com | http://flesler.blogspot.com
 * Licensed under BSD (http://www.opensource.org/licenses/bsd-license.php)
 * Date: 5/26/2008
 *
 * @projectDescription JS Class to translate text nodes.
 * @author Ariel Flesler
 * @version 1.0.1
 */
 
/**
 * The constructor must receive the parsing function, which will get the text as parameter
 * To use it, call the method .traverse() on the starting (root) node.
 * If the parsing is asynchronous (f.e AJAX), set sync to false on the instance.
 * When doing so, the parser function receives an extra argument, which is a function
 * that must be called passing it the parsed text.
 */
org.anotherearth.lib.Translator = function( parser, filter ){
	this.parse = parser; // function that parses the original string
	this.filter = filter; // optional filtering function that receives the node, and returns true/false
};
org.anotherearth.lib.Translator.prototype = {
	translate:function( old ){ // translates a text node
		if( this.sync )
			this.replace( old, this.parse(old.nodeValue) );
		else{
			var self = this;
			this.parse( old.nodeValue, function( text ){
				self.replace( old, text );
			});
		}
	},
	makeNode:function( data ){
		if( data && data.split ) // replacing for a string
			data = document.createTextNode(data);
		return data;
	},
	replace:function( old, text ){ // Replaces a text node with a new (string) text or another node
		if( text != null && text != old.nodeValue ){
			var parent = old.parentNode;
			if( text.splice ){ // Array
				for( var i = 0, l = text.length - 1; i < l; )
					parent.insertBefore( this.makeNode(text[i++]), old );
				text = this.makeNode(text[l] || ''); // Last
			}else
				text = this.makeNode(text);
			parent.replaceChild( text, old );
		}
	},
	valid:/\S/, // Used to skip empty text nodes (modify at your own risk)
	sync:true, // If the parsing requires a callback, set to false
	traverse:function( root ){ // Goes (recursively) thru the text nodes of the root, translating
		var children = root.childNodes,
			l = children.length,
			node;
		while( l-- ){
			node = children[l];
			if( node.nodeType == 3 ){ // Text node
				if( this.valid.test(node.nodeValue) ) // Skip empty text nodes
					this.translate( node );
			}else if( node.nodeType == 1 && (!this.filter || this.filter(node)) ) // Element node
				this.traverse( node );
		}
	}
};
