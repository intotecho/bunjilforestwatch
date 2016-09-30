import cache
import glad_data_seeder
from handlers.base_handlers import BaseHandler


class SeedGladClusterData(BaseHandler):

    def get(self):

        try:
            username = self.session['user']['name']
            user = cache.get_user(username)
            if not user:
                raise KeyError

        except KeyError:
            # TODO: use proper page redirects and redirect to login page.
            return self.response.write('You must be logged in as an administrator to seed glad cluster / case data')

        success, message = glad_data_seeder.seed_data(user)
        if success:
            self.response.set_status(200)
        else:
            self.response.set_status(400)

        return self.response.write(message)
