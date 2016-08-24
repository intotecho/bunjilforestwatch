from google.appengine.ext import ndb

class CompletedTask(ndb.model):
    datecompleted = ndb.DateTimeProperty(auto_now_add=True)
    username = ndb.StringProperty(required=True)
    caseid = ndb.StringProperty(required=True)
    caseresponse = ndb.StringProperty(required=True)


class UserTasksGoGetter(object):
    '''
    Handles communication with the server in searching for User's completed tasks
    '''

    list_completedtasks = []


class CaseGoGetter(object):
    '''
    Handles communication with the server in searching for Cases
    '''

    list_cases = []
    list_opencases = []

    def get_tasks(self, date):
