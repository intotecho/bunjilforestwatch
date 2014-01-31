//slight overhead checking and/or creating namespaces justified by removing dependency on script inclusion order

org = window.org || {};
org.anotherearth = window.org.anotherearth || {};
org.anotherearth.util = window.org.anotherearth.util || {};

org.anotherearth.util.Translator = {};
org.anotherearth.util.Translator.translatePage = function() {
	var browserLanguage = google.maps.Language.getLanguageCode();
	//convert text to browser language
	if (browserLanguage !== "en" && google.language.isTranslatable(browserLanguage)) {
		var parser = function(text, callback) {
			google.language.translate(text, "en", browserLanguage, function(result) {
				if (!result.error) { 
					result.translation = result.translation.replace(/&#\d{2};/, "");
					callback(result.translation);
				}
			});
		};

		var trans = new Translator(parser);
		trans.sync = false;
		trans.traverse($('body')[0]);
	}
};
