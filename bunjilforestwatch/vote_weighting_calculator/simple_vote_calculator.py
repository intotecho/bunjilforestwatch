
class SimpleVoteCalculator(object):

    def get_weighted_vote(self, user, case):
        return user.trust
