import models

from observation_task_routers import NextObservationTaskAjaxModel, BaseRouter


class PreferenceRouter(BaseRouter):
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
        Gets an array of open cases and an array of the user's preferences. Returns an observation task that aligns
        to the user's preferences if one is available, otherwise returns an observation task for any open case

        Args:
            user: The user currently in session

        Returns:
            The next observation task for a user to complete

        """

        open_cases_query = models.Case.query(models.Case.status == 'OPEN')
        user_preferences = models.ObservationTaskPreference.get_by_user_key(user.key)

        for open_case in open_cases_query:
            cluster = models.GladCluster.get_by_id(open_case.glad_cluster.id())
            area = models.AreaOfInterest.get_by_id(cluster.area.id())
            if self._case_is_not_already_completed_by_user(open_case, user) and (area.region in user_preferences.region_preference):
                return self._return_case_for_user(open_case)

        for open_case in open_cases_query:
            if self._case_is_not_already_completed_by_user(open_case, user):
                return self._return_case_for_user(open_case)

        return None

    def _return_case_for_user(self, case):
        """
        Args:
            case: the case to be served to the user

        Returns: the ajaxmodel object to be with appropriate parameters

        """
        cluster = models.GladCluster.get_by_id(case.glad_cluster.id())
        area = models.AreaOfInterest.get_by_id(cluster.area.id())
        overlays = cluster.overlays_entities
        return NextObservationTaskAjaxModel(case, cluster, area, overlays)
