

class CaseChecker(object):
    MAX_VOTES = 6
    MIN_CONSENSUS = 66

    @staticmethod
    def is_a_majority(self, case):
        maximum_value = 0
        total_votes = 0
        for category in case.votes:
            total_votes += category
            if category > maximum_value:
                maximum_value = category
        if maximum_value > 0:
            maximum_value = (maximum_value / total_votes) * 100
        if maximum_value > self.MIN_CONSENSUS:
            return True
        return False

    @staticmethod
    def is_max_votes(self, case):
        v = case.votes
        total_votes = (v.fire + v.agriculture + v.deforestation + v.road)
        if total_votes == self.MAX_VOTES:
            return True
        return False

