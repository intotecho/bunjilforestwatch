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
                return True
        return False

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

        for case_task in query1:
            if self._case_NOT_IN_completed_case(case_task, query2):

                "this is an expensive operation"
                cluster = models.GladCluster.get_by_id(case_task.glad_cluster.id())
                case = models.Case.get_by_id(case_task.key.id())
                area = cache.get_area_name_by_cluster_id(cluster.area.id())

                return NextObservationTaskAjaxModel(case, cluster, area)

        "still to be fixed"
        return None


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

        for case_task in query1:
            query2 = models.ObservationTasks.query(models.ObservationTasks.username == user.name, models.ObservationTasks.glad_cluster == case_task.glad_cluster)
            if query2.count == 0:

                cluster = models.GladCluster.get_by_id(case_task.glad_cluster.id())
                case = models.Case.get_by_id(case_task.key.id())
                area = cache.get_area(cluster.area.id())

                return NextObservationTaskAjaxModel(case, cluster, area)

        return NextObservationTaskAjaxModel('TODO', 'TODO', 'TODO')
