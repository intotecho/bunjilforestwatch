import models

from observation_task_routers import NextObservationTaskAjaxModel, BaseRouter
import cache


class SimpleRouter(BaseRouter):
    def __init__(self):
        pass

    def _case_NOT_IN_completed_case(self, open_case, completed_case_query):
        '''
        Args:
            open_case: A row from the Case table which has the status 'Open'
            completed_case_query: A query that returns all user completed cases

        Returns:
            Boolean return whether the case has been completed by the user

        '''
        for completed_task in completed_case_query:
            if open_case.glad_cluster == completed_task.glad_cluster:
                return True;
        return False;

    def _select_case_to_use_for_next_observation_task(self, user):
        '''
        Gets 2 arrays at the start of the method then compares them to each other

        Args:
            user: The user currently in session

        Returns:
            The row of the next case task if one is available

        '''
        # TODO: actually implement simple router selection

        query1 = models.Case.query(models.Case.status == 'OPEN')
        query2 = models.ObservationTasks.query(models.ObservationTasks.username == user.name)

        "THIS DOES NOT WORK - attempt at performing an IN on two queries"
        "query3 = query1.filter(models.Case.glad_cluster.IN[query2.filter(models.ObservationTasks.glad_cluster])"

        "Writes arbitrary data to observation tasks"
        for Case in query1:
            observation_task_entity = models.ObservationTasks(username=user.name, glad_cluster=Case.glad_cluster, caseresponse='Fire')
            observation_task_entity.put()

        for case_task in query1:
            if self._case_NOT_IN_completed_case(case_task, query2):
                return case_task

        return NextObservationTaskAjaxModel('TODO', 'TODO', 'TODO')


class SimpleRouter2(BaseRouter):
    def __init__(self):
        pass

    def _select_case_to_use_for_next_observation_task(self, user):
        '''
        Heavier network traffic version. Will need to speak to datastore for every row check

        Args:
            user: The user currently in session

        Returns:
            The row of the next case task if one is available

        '''
        # TODO: actually implement simple router selection

        query1 = models.Case.query(models.Case.status == 'OPEN')

        "THIS DOES NOT WORK - attempt at performing an IN on two queries"
        "query3 = query1.filter(models.Case.glad_cluster.IN[query2.filter(models.ObservationTasks.glad_cluster])"

        "Writes arbitrary data to observation tasks"
        for Case in query1:
            observation_task_entity = models.ObservationTasks(username=user.name, glad_cluster=Case.glad_cluster,
                                                              caseresponse='Fire')
            observation_task_entity.put()

        for case_task in query1:
            query2 = models.ObservationTasks.query(models.ObservationTasks.username == user.name, models.ObservationTasks.glad_cluster == case_task.glad_cluster)
            if query2.count == 0:
                return case_task

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