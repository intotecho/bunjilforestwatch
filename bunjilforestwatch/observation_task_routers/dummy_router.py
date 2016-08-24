import models
from observation_task_routers import NextObservationTaskAjaxModel, BaseRouter
import cache


class DummyRouter(BaseRouter):
    def __init__(self):
        pass

    def _select_case_to_use_for_next_observation_task(self, user):
        area = cache.get_area("Peru Seed")
        cluster = models.GladCluster.get_glad_clusters_for_area(area)[0]
        case = models.Case.get_cases_for_glad_cluster(cluster)[0]
        return NextObservationTaskAjaxModel(case, cluster, area)
