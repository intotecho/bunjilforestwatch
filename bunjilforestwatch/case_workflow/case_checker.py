from models import VOTE_CATEGORIES


class CaseChecker(object):
    MAX_VOTES = 6
    MIN_CONSENSUS = 66

    @staticmethod
    def is_a_majority(self, case):
        highest_vote = 0
        total_votes = 0
        for category in case.votes:
            total_votes += category
            if category > highest_vote:
                highest_vote = category
        if highest_vote > 0:
            highest_vote = (highest_vote / total_votes) * 100
        if highest_vote > self.MIN_CONSENSUS:
            return True
        return False

    @staticmethod
    def is_max_votes(self, case):
        v = case.votes
        total_votes = (v.fire + v.agriculture + v.deforestation + v.road)
        if total_votes == self.MAX_VOTES:
            return True
        return False

    @staticmethod
    def get_highest_category(self, case):
        """
        Returns the VOTE_CATAGORY that corresponds with the highest vote
        A possible bug is 50/50 splits
        """
        v = case.votes
        highest_vote = 0
        for category in v:
            if category > highest_vote:
                    highest_vote = category
        if highest_vote == 0:
            return "ERROR: No Majority detected"
        elif v.fire == highest_vote:
            return VOTE_CATEGORIES.FIRE
        elif v.agriculture == highest_vote:
            return VOTE_CATEGORIES.AGRICULTURE
        elif v.deforestation == highest_vote:
            return VOTE_CATEGORIES.DEFORESTATION
        elif v.road == highest_vote:
            return VOTE_CATEGORIES.ROAD
        elif v.unsure == highest_vote:
            return VOTE_CATEGORIES.UNSURE

