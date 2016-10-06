import models
from case_workflow.case_checker import CaseChecker
from notifications.local_subscriber_notifier import LocalSubscriberNotifier
from user_trust.user_trust_manager import UserTrustManager

checker = CaseChecker()
userTrustManager = UserTrustManager()
subscriberNotifier = LocalSubscriberNotifier()


# TODO: subscribe to case vote received event and spawn a thread
class CaseWorkflowManager(object):
    """
    Identifies when cases are eligible for closing and performs the case closing function
    """

    def __init__(self):
        pass

    def _close_case(self, case, status):
        """
        Closes a specified open case
        Args:
            case: An Open case that has been identified as suitable for closing
            status: The status the case is to be updated to
        """
        case.status = status
        case.put()
        userTrustManager.update_all_users_trust_async(case)
        subscriberNotifier.notify_subscribers_of_case_closure_async(case)

    def check_cases(self):
        """
        Identifies any classes suitable for closing and passes them to the close_case function
        """
        open_cases_query = models.Case.query(models.Case.status == models.OPEN)
        for open_case in open_cases_query:
            self.update_case_status(open_case)

    def update_case_status(self, case):
        """
        Args:
            case: An Open case that has been identified as a candidate for closing
        """
        update_case_state = models.OPEN
        if checker.is_min_votes(case):
            if checker.has_a_majority(case):
                update_case_state = models.CONFIRMED
            elif checker.is_max_votes(case):
                update_case_state = models.UNCONFIRMED
        if update_case_state != models.OPEN:
            self._close_case(case, update_case_state)
            # TODO: fire case closed event
