import json
import logging

import models
from handlers.base_handlers import BaseHandler


class ObsTaskPreferenceHandler(BaseHandler):
    """
    """
    def get(self):
        if 'user' in self.session:
            self.render('bfw-baseEntry-react.html')
        else:
            self.render('index.html', {
                'show_navbar': False
            })  # not logged in.


class ObsTaskPreferenceResource(BaseHandler):
    """
    This class defines the list of REST endpoints that are exposed for Preference data
    """

    def get(self):
        """Return a JSON of certain attributes in ObservationTaskPreference model

           Checks if User exists in session, then uses the User's key to obtain the preference data
           from the datastore which will be inserted into a JSON format and sent back as a response.
           """
        if 'user' in self.session:
            result = models.ObservationTaskPreference.get_by_user_key(self.session['user']['key'])

            if result:
                response = { "region_preference": result.region_preference }
            else:
                response = { "region_preference": [] }

            self.response.set_status(200)
            return self.response.write(json.dumps(response))
        else:
            logging.error('Cannot GET from ObsTaskPreferenceResource - user not found in session')
            return self.error(401)

    """Updates an ObservationTaskPreference data based on user_key and request payload

    Checks if User exists in session, then extracts the request payload in order to update
    the ObservationTaskPreference record that is bound by User's key.
    """
    def post(self):
        if 'user' in self.session:
            user_key = self.session['user']['key']
            response = json.loads(self.request.body)

            if response['region_preference'] is not None:
                models.ObservationTaskPreference.upsert(user_key, response['region_preference'])

                return self.response.set_status(200)
            else:
                logging.error('Cannot POST to ObsTaskPreferenceResource - region preferences not found')
                return self.error(400)
        else:
            logging.error('Cannot POST to ObsTaskPreferenceResource - user not found in session')
            return self.error(401)
