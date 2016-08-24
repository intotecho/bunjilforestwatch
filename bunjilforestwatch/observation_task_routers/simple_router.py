from observation_task_routers import NextObservationTaskAjaxModel, BaseRouter


class SimpleRouter(BaseRouter):
    def __init__(self):
        pass

    def _select_case_to_use_for_next_observation_task(self, user):
        # TODO: actually implement simple router selection
        return NextObservationTaskAjaxModel('TODO', 'TODO', 'TODO')
