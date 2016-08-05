
# PYTHON PACKAGES
This folder contains libraries that are used by the bunjilforestwatch project.
It does not contain libraries that Google App Engine includes via [app.yaml](https://github.com/intotecho/bunjilforestwatch/blob/master/bunjilforestwatch/app.yaml) library directives.

The files are all unmodified from published/released version. Generally the latest version of each library is used, although python versions later than 2.7.9 have an [issue](https://href.li/?https://code.google.com/p/googleappengine/issues/detail?id=12176) with SSL with the Windows 8 SDK at the moment (1.9.83 May 2016).

There is a workaround described here: https://code.google.com/p/googleappengine/issues/detail?id=12783

To resolve this issue, replace the file C:\Program Files (x86)\Google\google_appengine\google\appengine\dist27\socket.py
With the modified file sockets.py from the root folder of the bunjilforestwatch repo 

Files in lib are uploaded to appengine during deplyoment of the app, unless they are excluded in app.yaml.

After cloning this repo, the lib folder should be created by executing **pip** package manager commands in a script. 

cd to <$project$>/bunjilforestwatch/lib
pip install -U -t . -r requirements.txt

This will install all the libraries into the current folder /lib. 

 .gitignore is configured to  prevent these files being added to the repo.


