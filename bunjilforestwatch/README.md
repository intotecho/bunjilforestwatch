
# Bunjil Forest Watch
----
* Application: http://www.bunjilforestwatch.net
* Blog:        http://blog.bunjilforestwatch.net
* Jira:        http://bunjilforestwatch.atlassian.net (Issues Tracking)
* Contact:     chris [at] bunjilforestwatch.net (Chris Goodman, Developer)

# APPLICATION NOTES

Bunjil Forest Watch continuously checks for new satellite images covering a conservation area of interest. It scans public databases, such as LANDSAT images published at USGS. The boundary coordinates of an area to be monitored is provided by local conservation groups when they subscribe to the free service. When the solution finds new images covering their area it emails a volunteer to check for recent disturbances.

Volunteers review the latest images of an area and compare with older images. They mark-up any recent changes observed, such as new roads or clearings. The solution captures the coordinates of the change and sends a concise email or SMS report to the local group. The local group responds to the observed threats as they see fit.This service will connect local conservation groups in remote tropical regions with a network of volunteers who share the timely analysis of satellite images.

## DEVELOPER NOTES

Application runs on Google App Engine and uses Google Earth Engine.

If forking this app you will need to setup  a Google App Engine Account.

Earth Engine is still only available for limited release.
You also need to contact [Google Earth Engine](https://earthengine.google.org) to whitelist your service account before yoy can connect your app to earth engine.  Then generate an OAuth2 key for that service account. 
The Earth Engine API is under development and may change.

### Development Environment Setup Instructions for Windows
http://blog.bunjilforestwatch.net/learn/technology/dev-environment-setup-on-windows-pc/

## ISSUES LISTS

* PUBLIC: https://github.com/intotecho/bunjilforestwatch/issues
* CONTRIBUTORS: http://bunjilforestwatch.atlassian.net (requires login)

##BUILD DEPENDENCIES
These libraries are reuqired,
```sh
	apiclient/
	atom/
	docutils/
	dropbox/
	earthengine_api-0.1.61-py2.7.egg-info/
	ee/
	gdata/
	geodatastore/
	geojson/
	httplib2/
	httplib2-0.9.1-py2.7.egg-info/
	markdown.py
	markdown.pyc
	ndb/
	oauth2client/
	oauth2client-1.4.12-py2.7.egg-info/
	pyasn1/
	pyasn1-0.1.8-py2.7.egg-info/
	pyasn1_modules/
	pyasn1_modules-0.0.6-py2.7.egg-info/
	pyoauth.py
	pyoauth.pyc
	rainbow_logging_handler/
	roman.py
	roman.pyc
	rsa/
	rsa-3.1.4-py2.7.egg-info/
	rst_directive.pyc
	simplejson/
	simplejson-3.8.0-py2.7.egg-info/
	six-1.9.0.dist-info/
	six.py
	six.pyc
	textile.py*
	textile.pyc
	uritemplate/
```
