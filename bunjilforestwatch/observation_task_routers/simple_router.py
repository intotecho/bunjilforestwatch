import models

from observation_task_routers import NextObservationTaskAjaxModel, BaseRouter
import cache


class SimpleRouter(BaseRouter):
    def __init__(self):
        pass

    def _case_is_not_already_completed_by_user(self, open_case, user):
        """
        Args:
            open_case: A row from the Case table which has the status 'Open'
            user: the user to check against

        Returns:
            Boolean return whether the case has been completed by the user

        """
        result = models.ObservationTaskResponse.query()\
            .filter(models.ObservationTaskResponse.user == user.key)\
            .filter(models.ObservationTaskResponse.case == open_case.key).fetch()

        return len(result) == 0

    def _select_case_to_use_for_next_observation_task(self, user):
        """
        Gets 2 arrays at the start of the method then compares them to each other

        Args:
            user: The user currently in session

        Returns:
            The row of the next case task if one is available

        """

        open_cases_query = models.Case.query(models.Case.status == models.OPEN)

        for open_case in open_cases_query:
            if self._case_is_not_already_completed_by_user(open_case, user):
                cluster = models.GladCluster.get_by_id(open_case.glad_cluster.id())
                area = models.AreaOfInterest.get_by_id(cluster.area.id())
                overlays = cluster.overlays_entities
                return NextObservationTaskAjaxModel(open_case, cluster, area, overlays)

        return None
