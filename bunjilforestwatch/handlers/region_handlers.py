import json

import region_manager
from handlers.base_handlers import BaseHandler


class RegionHandler(BaseHandler):
    def get(self):
        return self.response.write(json.dumps(region_manager.get_regions()))