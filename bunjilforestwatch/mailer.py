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
        return ="chris@bunjilforestwatch.net"
    else:    
        return = "chris@bunjilforestwatch.net" 
   

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
    
    date_str = captured_date.strftime("%Y-%m-%d @ %H:%M")
    
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

        message.body = """
Dear  {0!s},

BUNJIL PROTOTYPE TASK NOTIFICATION !!!

A new image was taken on {1!s} of an area you follow: {3!s}.
 
Your new task is to check it for recent changes to forest cover and save your report by next {6!s} 

Please copy this link into your browser to start your task:
{2!s}">{2!s}</a><br><b>
Alternatively, visit {4!s} and navigate to mytasks

You are receiving this email because you have registered as a Bunjil Forest Watch Volunteer and are following the area {3!s}

To stop receiving emails you can unfollow the area or send an email to {5!s} with "UNSUBSCRIBE" in the subject.
From  Bunjil Forest Watch 
{4!s}
""".format(user.name, captured_date, task_url, task.aoi.string_id().encode('utf-8'), hosturl, thesender,completion_date )

        message.html = """
Dear  <b>{0!s}:</b><br><b>

<b>PROTOTYPE !!!</b><br>

A new image was taken on <i>{1!s}</i> of an area you follow: <b>{3!s}</b><br><br>
 
Your new task is to check it for recent changes to forest cover and save your report by next <b>{6!s}</b>.<br><br> 
Please click this link to start your task.<br>
<a href={2!s}>{2!s}</a><br><br><br>

You are receiving this email because you have registered as a Bunjil Forest Watch Volunteer and are following the area  <b>{3!s}</b>.<br>
To stop receiving emails you can unfollow the area or send an email to {5!s} with "UNSUBSCRIBE" in the subject.<br>
<a href="mailto:{5!s}u'?'subject=UNSUBSCRIBE" target="_top"></a><br>
<br>From <b><i><a href="{4!s}">Bunjil Forest Watch</a></b></i><br>
""".format(user.name, captured_date, task_url, task.aoi.string_id().encode('utf-8'), hosturl, thesender,completion_date )

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
