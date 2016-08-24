class NextObservationTaskAjaxModel(object):
    def __init__(self, case, glad_cluster, area):
        self.case = case
        self.glad_cluster = glad_cluster
        self.area = area


class BaseRouter(object):
    def _select_case_to_use_for_next_observation_task(self, user):
        pass

    def get_next_observation_task(self, user):
        return self._select_case_to_use_for_next_observation_task(user)
