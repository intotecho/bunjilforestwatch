import models

from observation_task_routers import NextObservationTaskAjaxModel, BaseRouter
import cache


class SimpleRouter(BaseRouter):
    def __init__(self):
        pass

    def _select_case_to_use_for_next_observation_task(self, user):
        # TODO: actually implement simple router selection

        query1 = models.Case.query(models.Case.status == 'OPEN')
        query2 = models.ObservationTasks.query(models.ObservationTasks.username == user.name)

        "THIS DOES NOT WORK - attempt at performing an IN on two queries"
        "query3 = query1.filter(models.Case.glad_cluster.IN[query2.filter(models.ObservationTasks.glad_cluster])"

        "Writes arbitrary data to observation tasks"
        for Case in query1:
            observation_task_entity = models.ObservationTasks(username=user.name, glad_cluster=Case.glad_cluster, caseresponse='Fire')
            observation_task_entity.put()





        return NextObservationTaskAjaxModel('TODO', 'TODO', 'TODO')


"""
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


class BaseRouter(object):
    def _select_case_to_use_for_next_observation_task(self, user):
        pass

    def get_next_observation_task(self, user):
        return self._select_case_to_use_for_next_observation_task(user)


class NextObservationTaskAjaxModel(object):
    def __init__(self, case, glad_cluster, area):
        self.case = case
        self.glad_cluster = glad_cluster
        self.area = area

"""