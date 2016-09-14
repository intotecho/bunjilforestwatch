from models import VOTE_CATEGORIES, Case, CaseVotes


class CaseChecker(object):
    MIN_VOTES_FOR_VIABLE_CONSENSUS = 6
    MIN_CONSENSUS = 66

    def has_a_majority(self, case):
        """
        :return: True: if the votes for a case form a clear majority for one vote category. Based on MIN_CONSENSUS
        and MIN_VOTES_FOR_VIABLE_CONSENSUS requirements.
        """
        highest_category_votes = 0
        total_votes = (case.votes.fire + case.votes.agriculture + case.votes.deforestation + case.votes.road)
        if case.votes.fire > highest_category_votes:
            highest_category_votes = case.votes.fire
        if case.votes.agriculture > highest_category_votes:
            highest_category_votes = case.votes.agriculture
        if case.votes.deforestation > highest_category_votes:
            highest_category_votes = case.votes.deforestation
        if case.votes.road > highest_category_votes:
            highest_category_votes = case.votes.road
        if case.votes.unsure == highest_category_votes:
            highest_category_votes = case.votes.unsure

        if highest_category_votes > 0:
            highest_category_votes = (highest_category_votes / total_votes) * 100
        if highest_category_votes > self.MIN_CONSENSUS:
            return True
        return False

    def is_min_votes(self, case):
        """
        :return: True if the case has the minimum number of votes for the consensus (or lack of consensus) to be
        considered viable for actioning (notifying local subscribers). False if more votes are required (e.g., a
        consensus of one vote is not very trustworthy).
        """
        total_votes = (case.votes.fire + case.votes.agriculture + case.votes.deforestation + case.votes.road)
        if total_votes >= self.MIN_VOTES_FOR_VIABLE_CONSENSUS:
            return True
        return False

    @staticmethod
    def get_most_voted_category(case):
        """
        Returns the VOTE_CATEGORY that corresponds with the highest vote
        A possible bug is 50/50 splits
        """
        highest_category_votes = 0

        if case.votes.fire > highest_category_votes:
            highest_category_votes = case.votes.fire
        if case.votes.agriculture > highest_category_votes:
            highest_category_votes = case.votes.agriculture
        if case.votes.deforestation > highest_category_votes:
            highest_category_votes = case.votes.deforestation
        if case.votes.road > highest_category_votes:
            highest_category_votes = case.votes.road

        if highest_category_votes == 0:
            return None
        elif case.votes.fire == highest_category_votes:
            return CaseVotes.fire
        elif case.votes.agriculture == highest_category_votes:
            return CaseVotes.agriculture
        elif case.votes.deforestation == highest_category_votes:
            return CaseVotes.deforestation
        elif case.votes.road == highest_category_votes:
            return CaseVotes.road

    @staticmethod
    def total_votes(self, case):
        """
        Can only take a case as an argument. This method factors unsure votes into total votes
        """
        result = (case.votes.fire + case.votes.agriculture + case.votes.deforestation + case.votes.road + case.votes.unsure)
        return result

    def closed_case_percentage_of_(self, category, case):
        """
        You must only pass in ClosedCase entities
        """
        vote_category = 0
        if category == VOTE_CATEGORIES.FIRE:
            vote_category = case.key().parent().fire
        if category == VOTE_CATEGORIES.DEFORESTATION:
            vote_category = case.key().parent().deforestation
        if category == VOTE_CATEGORIES.AGRICULTURE:
            vote_category = case.key().parent().agriculture
        if category == VOTE_CATEGORIES.ROAD:
            vote_category = case.key().parent().road
        if category == VOTE_CATEGORIES.UNSURE:
            vote_category = case.key().parent().unsure
        return (vote_category / self.total_votes(case)) * 100

