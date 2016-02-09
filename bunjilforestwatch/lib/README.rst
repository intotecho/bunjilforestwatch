# PYTHON PACKAGES
This folder contains libraries that are used by the bunjilforestwatch project.
It does not contain libraries that Google App Engine includes via [app.yaml](https://github.com/intotecho/bunjilforestwatch/blob/master/bunjilforestwatch/app.yaml) library directives.

The files are all unmodified from published/released version. Generally the latest version of each library is used, although python versions later than 2.7.9 have an [issue](https://href.li/?https://code.google.com/p/googleappengine/issues/detail?id=12176) with SSL with the Windows 8 SDK at the moment.

These files are uploaded to appengine during deplyoment of the app.

Instead of maintaining copies of these packages in this github repo, and downloading them, the  directory could instead be created by executing **pip** package manager commands in a script. 

- cd path/to/bunjilforestwatch/lib
- pip install -t . bleach
- pip install -t . docutils
 -pip install -t . ee
 -pip install -t . geojson
 -pip install -t . html5lib
 -pip install -t . httplib2
 -pip install -t . markdown
 -pip install -t . oauth2client
 -pip install -t . six

>However, this is not guranteed to be updated to be the correct list of commands, whereas the packages in the repo have been tested with the project.