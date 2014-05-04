import datetime
import logging



"""Mail Utilities - based on Rapleaf"""

from google.appengine.api import mail
import sys
import logging


#from email.utils import parseaddr

def new_image_email(user):

    thesender ="Postmaster@bunjilforestwatch.org"
    returnstr = ""
    try: 
        message = mail.EmailMessage(sender=thesender,
                                    subject="A new image is ready for your inspection")
        if user is not None:
            message.to = user.email
        else:
            massage.to = thesender #user does not exist
        message.body = """
Dear %s:

THIS IS JUST A TEST EMAIL. NO ACTION REQUIRED !!!

A new image is available for an area you follow: Gorilla Park.
The image was taken <Yesterday>.
Your task is to check it for recent changes to forest cover and file a report by next <Tuesday>. 
Click on this link  to complete your task.
http://bunjilforestwatch.org/user/recipient/task/123

You are receiving this email because you have registered as a Bunjil Forest Watch Volunteer and are following an area.

To stop receiving emails you can unfollow the area or send an email to postmaster@bunjilforestwatch.org with "UNSUBSCRIBE" in the subject.

Bunjil Forest Watch
http://bunjilforestwatch.org

    """ %user.name 

        message.send()
    except mail.InvalidEmailError:
        returnstr = 'Invalid email recipient.'
        return self.handle_error(returnstr)
        
    except mail.MissingRecipientsError:
        returnstr = 'You must provide a recipient.'
        return self.handle_error('You must provide a recipient.')
        
    except mail.MissingBodyError:
        returnstr ='You must provide a mail format.'
        return self.handle_error(returnstr)
            
    returnstr = "Sent mail to user: %s, with email: %s" %(user.name, message.to)
    logging.info(returnstr)    
    return returnstr
        


 

