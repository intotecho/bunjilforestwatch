from case_workflow.case_checker import CaseChecker
from notifications.email_sender import EmailSender
from time import gmtime, strftime


class LocalSubscriberNotifier(object):
    _email_sender = EmailSender()
    _case_checker = CaseChecker()

    def _get_local_subscribers(self, case):
        if case is not None:
            area = case.area
            return area.get_notification_subscribers() if area is not None else []

    def _get_case_closed_email_subject(self, case):
        if case is not None:
            threat = self._case_checker.get_most_voted_category(case).capitalize()
            if case.is_confirmed:
                return '{} threat has been identified'.format(threat)

            return '[Unconfirmed] {} threat has been identified'.format(threat)

    def _get_case_closed_email_content(self, case, recipient):
        if case is not None and recipient:
            threat = self._case_checker.get_most_voted_category(case).capitalize()
            if case.is_confirmed:
                return """Dear {},
                A {} threat has been detected in an area you have expressed interest in.

                Area Name: {}
                Case ID: {}
                Date: {}

                This message was sent by Bunjil Forest Watch
                """.format(recipient.name, threat, case.key.id(), case.area.name, strftime("%a, %d %b %Y %X %Z", gmtime()))

            # FIXME: show list of all potential options when there is little convergence
            return """Dear {},
                An UNCONFIRMED {} threat has been detected in an area you have expressed interest in.

                Area Name: {}
                Case ID: {}
                Date: {}

                This message was sent by Bunjil Forest Watch
                """.format(recipient.name, threat, case.key.id(), case.area.name,
                           strftime("%a, %d %b %Y %X %Z", gmtime()))

    def notify_subscribers_of_case_closure(self, case):
        """
        Notifies notification subscribers of the case area of the closure of the case.
        :param case: The case that has just been closed
        """
        if case is not None and case.is_closed and self._case_checker.total_votes(case) > 0:
            recipients = self._get_local_subscribers(case)
            subject = self._get_case_closed_email_subject(case)

            for recipient in recipients:
                content = self._get_case_closed_email_content(case, recipient)
                self._email_sender.send(recipient.email, subject, content)
