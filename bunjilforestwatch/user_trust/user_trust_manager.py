import logging

from google.appengine.api.taskqueue import InvalidTaskError
from google.appengine.ext.deferred import deferred

import models
from case_workflow import case_checker
from case_workflow.case_checker import CaseChecker
from number_utils import clamp


# TODO: subscribe to case closed event and spawn a thread
class UserTrustManager(object):
    """
    Updates the trust of all users who voted on the case that has just closed.
    """

    TRUST_MODIFIER_FOR_RESPONSE = 0.1
    PORTION_OF_MIN_VOTES_TO_USE_FOR_MAX_TRUST = 0.8

    checker = case_checker.CaseChecker()

    def __init__(self):
        pass

    def get_max_trust(self):
        """
        :return: The maximum trust that a user can have. This is a percentage of the minimum number of votes to
         close a case with a viable majority.
        """
        self.checker.get_min_votes_for_viable_consensus()
        return self.checker.get_min_votes_for_viable_consensus() * self.PORTION_OF_MIN_VOTES_TO_USE_FOR_MAX_TRUST

    def get_trust_modifier_for_response(self):
        """
        :return: The amount of trust that is gained or lost when the user responses correctly or incorrectly.
        """
        return self.TRUST_MODIFIER_FOR_RESPONSE;

    def _update_user_trust(self, user, case, response):
        if (user is not None) and (case is not None) and (response is not None):
            if response.vote_category != models.UNSURE:
                if response.vote_category.upper() == CaseChecker.get_most_voted_category(case):
                    trust_modifier = self.TRUST_MODIFIER_FOR_RESPONSE
                else:
                    trust_modifier = -self.TRUST_MODIFIER_FOR_RESPONSE

                new_trust = clamp(user.trust + trust_modifier, 0, self.get_max_trust())

                if user.trust != new_trust:
                    user.trust = new_trust
                    user.put()

    def _update_all_users_trust(self, case_id):
        case = models.Case.get_by_id(id=case_id)
        if case is not None and case.is_closed:
            task_responses = models.ObservationTaskResponse.query() \
                .filter(models.ObservationTaskResponse.case == case.key).fetch()
            logging.info('Updating {} user/s trust due to case {} closure'.format(str(len(task_responses)), str(case.key.id())))

            for response in task_responses:
                try:
                    self._update_user_trust(response.user.get(), case, response)
                except Exception:
                    pass

    def update_all_users_trust_async(self, case):
        """
        :param case: The case that has recently been closed.
        :return: When a case closes each user who voted on the case will have their trust modified based on whether
        the category they voted for. If the user voted for the category with the most votes then their trust will
        increase and will decrease if they selected a lesser chosen category.

        NOTE: This task will only be completed once per case.
        """
        try:
            deferred.defer(self._update_all_users_trust, case.key.id(), _countdown=10, _queue='update-user-trust-queue',
                           _name='closed-{}'.format(case.non_unique_task_name))
        except InvalidTaskError:
            pass
