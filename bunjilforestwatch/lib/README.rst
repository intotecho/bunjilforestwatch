
# PYTHON PACKAGES
This folder contains libraries that are used by the bunjilforestwatch project.
It does not contain libraries that Google App Engine includes via [app.yaml](https://github.com/intotecho/bunjilforestwatch/blob/master/bunjilforestwatch/app.yaml) library directives.

The files are all unmodified from published/released version. Generally the latest version of each library is used, although python versions later than 2.7.9 have an [issue](https://href.li/?https://code.google.com/p/googleappengine/issues/detail?id=12176) with SSL with the Windows 8 SDK at the moment.

These files are uploaded to appengine during deplyoment of the app.

Instead of maintaining copies of these packages in this github repo, and downloading them, the  directory could instead be created by executing **pip** package manager commands in a script. 

cd to <$project$>/bunjilforestwatch/lib
pip install -U -t . -r requirements.txt

This will install all the libraries into the lib folder. 

The gitignore should prevent these files being added to the repo.

