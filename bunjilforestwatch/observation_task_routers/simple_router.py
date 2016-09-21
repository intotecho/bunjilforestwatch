import models

from observation_task_routers import NextObservationTaskAjaxModel, BaseRouter
import cache


class SimpleRouter(BaseRouter):
    def __init__(self):
        pass

    def _case_is_not_already_completed_by_user(self, open_case, completed_tasks_query):
        """
        Args:
            open_case: A row from the Case table which has the status 'Open'
            completed_tasks_query: A query that returns all user completed cases

        Returns:
            Boolean return whether the case has been completed by the user

        """
        for completed_task in completed_tasks_query:
            if open_case.key == completed_task.case:
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
            .query(models.ObservationTaskResponse.userid == user.uid)

        for open_case in open_cases_query:
            if self._case_is_not_already_completed_by_user(open_case, completed_tasks_query):
                cluster = models.GladCluster.get_by_id(open_case.glad_cluster.id())
                # case = models.Case.get_by_id(open_case.key.id())
                area = models.AreaOfInterest.get_by_id(cluster.area.id())

                return NextObservationTaskAjaxModel(open_case, cluster, area)

        return None
