from user_trust.user_trust_manager import UserTrustManager

user_trust_manager = UserTrustManager()


class SimpleVoteCalculator(object):
    """
    Represents the number of seconds that has to pass in order for the user's
    maximum trust value to be realized
    """
    TASK_DURATION_SECONDS_THRESHOLD = 5.0

    def get_weighted_vote(self, user, case, task_duration_seconds=0.01):
        """
        IF trust is greater than threshold number THEN
        We do not consider task_duration_seconds in weighting
        """
        if user.trust > self.get_user_trust_threshold():
            return user.trust
        else:
            if task_duration_seconds > self.TASK_DURATION_SECONDS_THRESHOLD:
                task_duration_seconds = self.TASK_DURATION_SECONDS_THRESHOLD

            """
            Return user's trust value based on the amount of task_duration_seconds
            Each second provides a full 20% value of trust
            """
            return self.get_task_duration_vote_modifier(user.trust, task_duration_seconds)

    def get_task_duration_vote_modifier(self, trust_value, task_duration_seconds):
        return trust_value * (task_duration_seconds / self.TASK_DURATION_SECONDS_THRESHOLD)

    def get_user_trust_threshold(self):
        """
        :return: The amount of trust that is gained or lost when the user responses correctly or incorrectly.
        """
        return user_trust_manager.get_max_trust() * 0.2
