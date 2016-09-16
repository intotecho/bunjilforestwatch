class SimpleVoteCalculator(object):
  USER_TRUST_THRESHOLD = 10
  TIME_SPENT_THRESHOLD = 5.0 # In seconds

  def get_weighted_vote(self, user, case, time_spent=0.0):
    # IF trust is greater than threshold number THEN
    # We do not consider time_spent in weighting
    if user.trust > SimpleVoteCalculator.USER_TRUST_THRESHOLD:
      return user.trust
    else:
      if time_spent > SimpleVoteCalculator.TIME_SPENT_THRESHOLD:
        time_spent = SimpleVoteCalculator.TIME_SPENT_THRESHOLD
      elif time_spent == 0:
        # Prevent division by zero
        time_spent = 0.01

      # Return user's trust value based on the amount of time_spent
      # Each second provides a full 20% value of trust
      return user.trust * (time_spent / SimpleVoteCalculator.TIME_SPENT_THRESHOLD)
