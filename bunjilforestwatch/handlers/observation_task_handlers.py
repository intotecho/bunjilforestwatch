import json
import logging

import cache
import case_workflow
import models
from handlers.base_handlers import BaseHandler
from observation_task_routers.dummy_router import DummyRouter
from observation_task_routers.preference_router import PreferenceRouter
from observation_task_routers.simple_router import SimpleRouter
from vote_weighting_calculator.simple_vote_calculator import SimpleVoteCalculator


class ObservationTaskHandler(BaseHandler):
    def get(self, router_name='REGION_PREFERENCE'):

        try:
            username = self.session['user']['name']
            user = cache.get_user(username)
            if not user:
                raise KeyError
                # TODO: use proper page redirects and redirect to login page.

        except KeyError:
            return self.response.write('You must be logged in!')

        router = None
        if router_name == 'DUMMY':
            router = DummyRouter()
        elif router_name == 'SIMPLE':
            router = SimpleRouter()
        elif router_name == "REGION_PREFERENCE":
            router = PreferenceRouter()
        else:
            result_str = "Specified router not found"
            logging.error(result_str)
            self.response.set_status(404)
            return self.response.write(result_str)

        result = router.get_next_observation_task(user)
        if result is None:
            self.response.set_status(404)
            return self.response.write("No uncompleted tasks available")

        return self.response.write(result.to_JSON())
        self.response.set_status(200)

    def post(self):
        """
            Accepts an observation task response

            Example request body
            {
                "vote_category": "FIRE",
                "case_id": 4573418615734272
            }
        :return:
        """
        try:
            username = self.session['user']['name']
            user = cache.get_user(username)
            if not user:
                raise KeyError

        except KeyError:
            self.response.set_status(401)
            return

        observation_task_response = json.loads(self.request.body)
        # TODO: use a json encoder and us a Decoding Error for the validation
        if observation_task_response['vote_category'] is not None:
            if observation_task_response['case_id'] is not None:
                # TODO: consider moving this check down into a JSON decoding function or BLL module
                if observation_task_response['vote_category'] in models.VOTE_CATEGORIES:
                    case = models.Case.get_by_id(id=observation_task_response['case_id'])
                    if case is None:
                        # TODO: consider moving this check down into a BLL module
                        self.response.set_status(404)
                        return

                    # Check if user has already completed task
                    if models.ObservationTaskResponse \
                            .query(models.ObservationTaskResponse.user == user.key,
                                   models.ObservationTaskResponse.case == case.key).fetch():
                        self.response.set_status(400)
                        return

                    observation_task_entity = models.ObservationTaskResponse(user=user.key,
                                                                             case=case.key,
                                                                             vote_category=
                                                                             observation_task_response['vote_category'],
                                                                             case_response=
                                                                             observation_task_response,
                                                                             task_duration_seconds=
                                                                             observation_task_response[
                                                                                 'task_duration_seconds'])
                    observation_task_entity.put()

                    vote_calculator = SimpleVoteCalculator()
                    case.votes.add_vote(observation_task_response['vote_category'],
                                        vote_calculator.get_weighted_vote(
                                            user, case, observation_task_response['task_duration_seconds']))
                    case.put()

                    case_manager = case_workflow.case_workflow_manager.CaseWorkflowManager()
                    case_manager.update_case_status(case)

                    self.response.set_status(201)

                    return

        self.reponse.set_status(400)
        return
