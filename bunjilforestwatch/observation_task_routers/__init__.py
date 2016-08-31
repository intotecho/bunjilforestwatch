import json


class NextObservationTaskAjaxModel(object):
    def __init__(self, case, glad_cluster, area):
        self.case = case.to_dict(exclude=['glad_cluster', 'creation_time'])
        self.case['case_id'] = case.key.id()
        self.glad_cluster = {
            "cluster_id": glad_cluster.key.id(),
            "geojson": glad_cluster.geojson
        }
        self.area_id = area.key.id()

    def to_JSON(self):
        return json.dumps({
            "case": self.case,
            "glad_cluster": self.glad_cluster,
            "area_id": self.area_id
        })


class BaseRouter(object):
    def _select_case_to_use_for_next_observation_task(self, user):
        pass

    def get_next_observation_task(self, user):
        return self._select_case_to_use_for_next_observation_task(user)
