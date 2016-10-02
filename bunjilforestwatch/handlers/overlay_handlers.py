import json
import logging

import cache
import models
from handlers.base_handlers import BaseHandler
import overlay_manager


class RegenerateOverlayHandler(BaseHandler):
    """
    Regenerates expired overlays. When an overlay is regenerated it receives new map_id and token values.
    """

    def get(self, overlay_key):

        overlay = models.Overlay.get_from_encoded_key(overlay_key)
        if not overlay:
            logging.error('RegenerateOverlayHandler Could not find Image')
            self.response.set_status(404)
            return

        logging.debug('RegenerateOverlayHandler() visualization of image %s from collection :%s', overlay.map_id,
                      overlay.image_collection)
        overlay = overlay_manager.regenerate_overlay(overlay)
        if overlay is None or overlay.map_id is None:
            logging.error('RegenerateOverlayHandler Could not regenerate overlay')
            self.response.set_status(404)
            return

        cache.set_keys([overlay])
        logging.debug('RegenerateOverlayHandler() updated ' + overlay.image_id + ' ' + overlay.algorithm + ' overlay')
        self.populate_user_session()
        self.response.set_status(200)
        self.response.write(json.dumps(overlay.to_dict))
