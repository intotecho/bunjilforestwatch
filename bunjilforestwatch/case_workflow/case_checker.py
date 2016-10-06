from models import VOTE_CATEGORIES, Case, CaseVotes, FIRE, AGRICULTURE, DEFORESTATION, ROAD


class CaseChecker(object):
    MIN_VOTES_FOR_VIABLE_CONSENSUS = 6
    MAX_VOTES = 12
    MIN_CONSENSUS = 66

    def get_min_votes_for_viable_consensus(self):
        return self.MIN_VOTES_FOR_VIABLE_CONSENSUS

    def has_a_majority(self, case):
        """
        :return: True: if the votes for a case form a clear majority for one vote category. Based on MIN_CONSENSUS
        and MIN_VOTES_FOR_VIABLE_CONSENSUS requirements.

        If the majority category is models.UNSURE then false will be returned as this is not considered a valid majority.
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
        total_votes = self.total_votes(case)
        if highest_category_votes > 0:
            highest_votes = (highest_category_votes / total_votes) * 100
        if highest_votes > self.MIN_CONSENSUS:
            return True
        return False

    def is_min_votes(self, case):
        """
        :return: True if the case has the minimum number of votes for the consensus (or lack of consensus) to be
        considered viable for actioning (notifying local subscribers). False if more votes are required (e.g., a
        consensus of one vote is not very trustworthy).
        """
        total_votes = self.total_votes(case)
        if total_votes >= self.MIN_VOTES_FOR_VIABLE_CONSENSUS:
            return True
        return False

    def is_max_votes(self, case):
        """
        Returns:
            result: a boolean representing if a case has reached maximum votes
        Args:
            case: a case data store entry
        """
        if self.total_votes(case) >= self.MAX_VOTES:
            return True
        return False

    @staticmethod
    def get_most_voted_category(case):
        """
        Returns the VOTE_CATEGORY that corresponds with the highest vote
        A possible bug is 50/50 splits

        If highest voted category is models.UNSURE then the second highest category will be returned.
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
            return FIRE
        elif case.votes.agriculture == highest_category_votes:
            return AGRICULTURE
        elif case.votes.deforestation == highest_category_votes:
            return DEFORESTATION
        elif case.votes.road == highest_category_votes:
            return ROAD

    @staticmethod
    def total_votes(case):
        """
        Returns:
            result: a float value of all votes tallied together. NOTE: this count includes the unsure votes.
        Args:
            case: a case data store entry
        """
        result = (case.votes.fire + case.votes.agriculture + case.votes.deforestation + case.votes.road + case.votes.unsure)
        return result

    def closed_case_percentage_of_(self, category, case):
        """
        Returns:
            The percentage that a vote category for a closed case received
        Args:
            category: the category of votes to be returned
            case: a closed case
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



