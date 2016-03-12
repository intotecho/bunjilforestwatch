#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import logging
import cache

"""Mail Utilities - based on Rapleaf"""

from google.appengine.api import mail
import sys
import logging
import os
from os import environ

#from email.utils import parseaddr

def mail_sender():
    if os.environ['SERVER_SOFTWARE'].startswith('Development'): 
        return "chris@bunjilforestwatch.net"
    else:    
        return "chris@bunjilforestwatch.net" 
   

def new_image_email(task, hosturl):

    thesender = []
    returnstr = ""
    thesender =mail_sender()
    
    if task is None:
        returnstr = "new_image_email: no task to send"
        logging.error(returnstr)
        return False

    user_key = task.assigned_owner
    if user_key is None:
        returnstr = "new_image_email: no user key assigned to send"
        logging.error(returnstr)
        return returnstr
    user=user_key.get()
    if user is None:
        returnstr = "new_image_email: no user assigned to send"
        logging.error(returnstr)
        return returnstr
    
    aoi = task.aoi
    if aoi is None:
        returnstr = "new_image_email: no AOI in task"
        logging.error(returnstr)
        return returnstr
    
    ok = task.observations[0]
    obs = ok.get() #cache.get_by_key(ok)
    if obs is None:
        returnstr = "new_image_email: task has no observations"
        logging.error(returnstr)
        return returnstr
    
    #captured_date = datetime.datetime.fromtimestamp(obs.captured) #convert ms
    captured_date = obs.captured #convert ms
    completion_date = captured_date + datetime.timedelta(3,0)
    captured_str = '{0:%B} {0:%d}'.format(captured_date)
    completion_date_str = '{0:%B} {0:%d}'.format(completion_date)

    #date_str = captured_date.strftime("%Y-%m-%d @ %H:%M")
    
    task_url = task.taskurl() #hosturl + "/obs/" + user.name + "/" + str(task.key())
    #print task_url
    
    if len(task.observations) == 1:
        subject = "A new image {0!s} is ready for your inspection".format(obs.image_id)
    else:
        subject = "New images are ready for your inspection including: {0!s}".format(obs.image_id)

    try: 
        message = mail.EmailMessage(sender=thesender, subject=subject)
        
        if user is not None and user.email is not None:
            message.to = user.email
        else:
            message.to = thesender #user does not exist

        message.body = ("\n"
                        "{0!s}, \n\n"
                        "You have a new task from Bunjil Forest Watch.\n"
                        "\n"
                        "A new image was captured on {1!s} for an area you follow: {3!s}.\n"
                        " \n"
                        "Your task is to check it for recent changes to forest cover and save your report by {6!s}. \n"
                        "\n"
                        "Copy this link into your browser to start the task:\n"
                        "{4!s}{2!s}\n\n"
                        "Alternatively, visit {4!s} and navigate to mytasks\n\n"
                        "You are receiving this email because you have registered as a Bunjil Forest Watch Volunteer and are following the area '{3!s}'\n\n"
                        "To stop receiving emails about tasks for this area, go to the application and stop watching this area.<br>\n"
                        "Or forward this email to {5!s} with \"UNSUBSCRIBE\" in the subject.\n\n"
                        "This is an automatically generated email from Bunjil Forest Watch \n\n"
                        "{4!s}\n").format(user.name, captured_str, task_url, task.aoi.string_id().encode('utf-8'), hosturl, thesender, completion_date_str)

        message.html = ("\n"
                        "<b>{0!s}</b>,<br/>\n"
                        "\n"
                        "<em>Bunjil Forest Watch</em> assigned a new task to you.\n"
                        "\n"
                        "A new image was captured on <i>{1!s}</i> for the area you follow: <b>{3!s}</b><br/><br/>\n"
                        " \n"
                        "Your task is to check it for recent changes to forest cover and submit a report by <b>{6!s}</b>.<br><br> \n"

                        "Click to <a href={4!s}{2!s}>start your task</a>.<br/><br/><br/>\n"
                        "\n"
                        "You are receiving this email because you have registered as a <em>Bunjil Forest Watch Volunteer</em> and are following the area "
                        "<a href={4!s}{7!s}>{3!s}</a>.<br/><br/>\n"
                        "To stop receiving emails about tasks for this area, \n"
                        "<a href={4!s}{7!s}/follow?unfollow=true>stop watching</a> this area.<br>"
                        "Alternatively forward this email to {5!s} with \"UNSUBSCRIBE\" in the subject.<br>\n"
                        "<a href=\"mailto:{5!s}?subject=UNSUBSCRIBE\" target=\"_top\"></a><br>\n"
                        "<br>This is an automatically generated email from <b><i><a href=\"{4!s}\">Bunjil Forest Watch</a></b></i><br>\n").format(
            user.name,
            captured_str,
            task_url,
            task.aoi.string_id().encode('utf-8'),
            hosturl,
            thesender,
            completion_date_str,
            task.aoi.get().url()
        )
        try:
            message.send()
        except:
            returnstr = "SMTP ERROR - Could not send mail Sent mail to user: {0!s}, with email: {1!s} from sender: {2!s} with subject: {3!s}".format(user.name, message.to, thesender, message.subject)
            logging.error(returnstr)
            logging.debug(message.html)
            returnstr += "<br> {0!s}".format(message.html)
            return returnstr

    except mail.InvalidEmailError:
        returnstr = 'Invalid email recipient.'
        logging.error(returnstr)    
        return returnstr
        
    except mail.MissingRecipientsError:
        returnstr = 'No recipient provided.'
        logging.error(returnstr)    
        return returnstr
        
    except mail.MissingBodyError:
        returnstr ='No mail format provided.'
        logging.error(returnstr)    
        return returnstr
    
    except mail.MissingSubjectError:
        returnstr ='Missing email subject.'
        logging.error(returnstr)    
        return returnstr
    
    except mail.MissingBodyError:
        returnstr ='Missing body.'
        logging.error(returnstr)    
        return returnstr
    
    except mail.InvalidSenderError:
        returnstr ='Invalid sender.'
        logging.error(returnstr)    
        return returnstr

    except mail.BadRequestError:
        returnstr ='Invalid email rejected.'
        logging.error(returnstr)    
        return returnstr

    except:
        returnstr ='Error sending email.'
        logging.error(returnstr)    
        return returnstr

    returnstr = "Sent mail to user: {0!s}, with email: {1!s} from sender: {2!s} with subject: {3!s}".format(user.name, message.to, thesender, message.subject)
    logging.info(returnstr)    
    returnstr += "<br> {0!s}".format(message.html)
    return returnstr


def new_user_email(user):

    thesender = []
    returnstr = ""
    thesender = mail_sender() 
   
    if user is None:
        returnstr = "new_user_email: no user assigned to send"
        logging.error(returnstr)
        return returnstr
    
    
    subject = "A new user {0!s} has signed in email: {1!s} ".format(user.name, user.email)
    
    try: 

        message = mail.EmailMessage(sender=thesender, subject=subject)
        message.to = thesender
        
        message.body = """

BUNJIL FOREST WATCH NEW USER !!!

A new user {0!s} has signed in email: {1!s} "

""".format(user.name, user.email)

        message.send()
        
    except mail.InvalidEmailError:
        returnstr = 'Invalid email recipient.'
        logging.error(returnstr)    
        return returnstr
        
    except mail.MissingRecipientsError:
        returnstr = 'No recipient provided.'
        logging.error(returnstr)    
        return returnstr
        
    except mail.MissingBodyError:
        returnstr ='No mail format provided.'
        logging.error(returnstr)    
        return returnstr
    
    except mail.MissingSubjectError:
        returnstr ='Missing email subject.'
        logging.error(returnstr)    
        return returnstr
    
    except mail.MissingBodyError:
        returnstr ='Missing body.'
        logging.error(returnstr)    
        return returnstr
    
    except mail.InvalidSenderError:
        returnstr ='Invalid sender.'
        logging.error(returnstr)    
        return returnstr

    except mail.BadRequestError:
        returnstr ='Invalid email rejected.'
        logging.error(returnstr)    
        return returnstr

    except:
        returnstr ='Error sending email.'
        logging.error(returnstr)    
        return returnstr

    returnstr = "Sent mail to user: {0!s}, with email: {1!s} from sender: {2!s} with subject: {3!s}".format(user.name, message.to, thesender, message.subject)
    logging.info(returnstr)    
    returnstr += "<br> {0!s}".format(message.body)
    return returnstr
