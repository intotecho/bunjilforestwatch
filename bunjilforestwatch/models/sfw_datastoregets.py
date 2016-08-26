from google.appengine.ext import ndb
import models


class UserTasksGoGetter(object):
    '''
    Handles communication with the server in searching for User's completed tasks
    '''

    def empty(self):
        if self.query().fetch(keysonly=True) == 0:
            return True
        return False

    def addcompletedtask(self, name, caseid, caseresponse):
        if not self.empty():
            first_entry = self.query().fetch(1)
            if first_entry.get("username") != name:
                return
            else:
                "write to database here"
        else:
            return

    def get_tasks(self, name):
        caselist = UserCompletedCases





class CaseGoGetter(object):
    '''
    Handles communication with the server in searching for Cases
    '''

    list_cases = []
    list_opencases = []

    def get_tasks(self, date):
