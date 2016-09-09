

import case_checker
import models

checker = case_checker.CaseChecker
Case = models.Case
ClosedCase = models.ClosedCase


class CaseWorkflowManager(object):
    def __init__(self):
        pass

    @staticmethod
    def update_case(self, case):
        """Do some stuff"""
        pass

    @staticmethod
    def close_case(self, case, majority_held):
        """Do some stuff"""
        ClosedCase.add(case, majority_held)

    def check_cases(self):
        open_cases_query = Case.query(Case.status == 'OPEN')
        for open_case in open_cases_query:
            update_case_state = False
            if open_case is not None:
                if checker.is_min_votes(open_case):
                    if checker.has_a_majority(open_case):
                        update_case_state = True
                if update_case_state:
                    self.update_case(open_case)

