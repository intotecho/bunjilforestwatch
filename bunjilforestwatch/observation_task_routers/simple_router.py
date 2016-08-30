import models

from observation_task_routers import NextObservationTaskAjaxModel, BaseRouter
import cache


class SimpleRouter(BaseRouter):
    def __init__(self):
        pass

    # TODO: consider renaming to case task is not already completed by user
    def _case_NOT_IN_completed_case(self, open_case, completed_tasks_query):
        """
        Args:
            open_case: A row from the Case table which has the status 'Open'
            completed_tasks_query: A query that returns all user completed cases

        Returns:
            Boolean return whether the case has been completed by the user

        """
        for completed_task in completed_tasks_query:
            # TODO: consider if open_case.key == completed_task.case:
            if open_case.glad_cluster == completed_task.glad_cluster:
                return False
        return True

    def _select_case_to_use_for_next_observation_task(self, user):
        """
        Gets 2 arrays at the start of the method then compares them to each other

        Args:
            user: The user currently in session

        Returns:
            The row of the next case task if one is available

        """

        open_cases_query = models.Case.query(models.Case.status == 'OPEN')
        completed_tasks_query = models.ObservationTaskResponse\
            .query(models.ObservationTaskResponse.username == user.name)

        for open_case in open_cases_query:
            if self._case_NOT_IN_completed_case(open_case, completed_tasks_query):
                cluster = models.GladCluster.get_by_id(open_case.glad_cluster.id())
                # case = models.Case.get_by_id(open_case.key.id())
                area = models.AreaOfInterest.get_by_id(cluster.area.id())

                return NextObservationTaskAjaxModel(open_case, cluster, area)

        return None


class SimpleRouter2(BaseRouter):
    def __init__(self):
        pass

    def _select_case_to_use_for_next_observation_task(self, user):
        """
        Heavier network traffic version. Will need to speak to datastore for every row check

        Args:
            user: The user currently in session

        Returns:
            The row of the next case task if one is available

        """

        query1 = models.Case.query(models.Case.status == 'OPEN')

        for case_task in query1:
            query2 = models.ObservationTaskResponse.query(models.ObservationTaskResponse.username == user.name,
                                                          models.ObservationTaskResponse.glad_cluster == case_task.glad_cluster)
            if query2.count == 0:
                cluster = models.GladCluster.get_by_id(case_task.glad_cluster.id())
                case = models.Case.get_by_id(case_task.key.id())
                area = cache.get_area(cluster.area.id())

                return NextObservationTaskAjaxModel(case, cluster, area)

        return NextObservationTaskAjaxModel('TODO', 'TODO', 'TODO')
