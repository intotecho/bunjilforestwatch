#from sendgrid.helpers.mail import mail
#from sendgrid.helpers import mail

import sendgrid
import os
from sendgrid.helpers.mail import *

import secrets


class EmailSender(object):
    _sender = sendgrid.SendGridAPIClient(apikey=secrets.SENDGRID_API_KEY)

    def send(self, recipient, subject, content):
        """
        :param recipient: The email recipient
        :param subject: The message that appears in the subject line of the email
        :param content: The body of the email
        """
        message = mail.Mail(mail.Email(secrets.SENDGRID_SENDER), subject, mail.Email(recipient),
                            mail.Content('text/plain', content))
        self._sender.client.mail.send.post(request_body=message.get())

    def send_to_all(self, recipients, subject, content):
        """
        :param recipients: The email recipients
        :param subject: The message that appears in the subject line of the email
        :param content: The body of the email
        """
        from_email = mail.Email(secrets.SENDGRID_SENDER)
        content = mail.Content('text/plain', content)

        for recipient in recipients:
            to_email = mail.Email(recipient)
            message = mail.Mail(from_email, subject, to_email, content)
            self._sender.client.mail.send.post(request_body=message.get())
