import case_checker
import models

checker = case_checker.CaseChecker()
Case = models.Case


class CaseWorkflowManager(object):
    """
    Identifies when cases are eligible for closing and performs the case closing function
    """
    def __init__(self):
        pass

    def _close_case(self, case):
        """
        Closes a specified open case
        Args:
            case: An Open case that has been identified as suitable for closing
        """
        case.status = "CLOSED"
        case.put()

    def check_cases(self):
        """
        Identifies any classes suitable for closing and passes them to the close_case function
        """
        open_cases_query = Case.query(Case.status == 'OPEN')
        for open_case in open_cases_query:
            self.update_case_status(open_case)

    def update_case_status(self, case):
        """
        Args:
            case: An Open case that has been identified as a candidate for closing
        """
        update_case_state = False
        if checker.is_min_votes(case):
            if checker.has_a_majority(case):
                update_case_state = True
        if update_case_state:
            self._close_case(case)