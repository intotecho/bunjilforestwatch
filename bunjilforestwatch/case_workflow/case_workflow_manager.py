

import case_checker
import models

checker = case_checker.CaseChecker
Case = models.Case


class CaseWorkflowManager(object):
    def __init__(self):
        pass

    @staticmethod
    def update_case(self, case):
        """Do some stuff"""
        self.close_case(case, checker.get_most_voted_category(case))

    @staticmethod
    def close_case(self, case, majority_held):
        """Do some stuff"""
        case.status = 'CLOSED'

    def check_cases(self):
        open_cases_query = Case.query(Case.status == 'OPEN')
        for open_case in open_cases_query:
            update_case_state = False
            if open_case is not None:
                if checker.is_min_votes(checker, open_case):
                    if checker.has_a_majority(checker, open_case):
                        update_case_state = True
                if update_case_state:
                    self.update_case(open_case)

    def check_single_case(self, case):
        update_case_state = False
        if checker.is_min_votes(checker, case):
            if checker.has_a_majority(checker, case):
                update_case_state = True
        if update_case_state:
            self.update_case(case)