from models import VOTE_CATEGORIES


class CaseChecker(object):
    MIN_VOTES_FOR_VIABLE_CONSENSUS = 6
    MIN_CONSENSUS = 66

    @staticmethod
    def has_a_majority(self, case):
        """
        :return: True: if the votes for a case form a clear majority for one vote category. Based on MIN_CONSENSUS
        and MIN_VOTES_FOR_VIABLE_CONSENSUS requirements.
        """
        highest_category_votes = 0
        total_votes = 0
        for category_votes in case.votes:
            total_votes += category_votes
            if category_votes > highest_category_votes:
                highest_category_votes = category_votes
        if highest_category_votes > 0:
            highest_category_votes = (highest_category_votes / total_votes) * 100
        if highest_category_votes > self.MIN_CONSENSUS:
            return True
        return False

    @staticmethod
    def is_min_votes(self, case):
        """
        :return: True if the case has the minimum number of votes for the consensus (or lack of consensus) to be
        considered viable for actioning (notifying local subscribers). False if more votes are required (e.g., a
        consensus of one vote is not very trustworthy).
        """
        case_votes = case.votes
        total_votes = (case_votes.fire + case_votes.agriculture + case_votes.deforestation + case_votes.road)
        if total_votes == self.MAX_VOTES:
            return True
        return False

    @staticmethod
    def get_most_voted_category(case):
        """
        Returns the VOTE_CATEGORY that corresponds with the highest vote
        A possible bug is 50/50 splits
        """
        case_votes = case.votes
        highest_category_votes = 0
        for category in case_votes:
            if category > highest_category_votes:
                    highest_category_votes = category
        if highest_category_votes == 0:
            return None
        elif case_votes.fire == highest_category_votes:
            return VOTE_CATEGORIES.FIRE
        elif case_votes.agriculture == highest_category_votes:
            return VOTE_CATEGORIES.AGRICULTURE
        elif case_votes.deforestation == highest_category_votes:
            return VOTE_CATEGORIES.DEFORESTATION
        elif case_votes.road == highest_category_votes:
            return VOTE_CATEGORIES.ROAD
        elif case_votes.unsure == highest_category_votes:
            return VOTE_CATEGORIES.UNSURE

