from collections import defaultdict


class AsyaSupervisor:
    """
    Supervisor for running the Asya gathering async procedure.
    It contains some procedure-wide setting and calls.

    The ``gather_acquaintances`` function must call supervisor's
    ``report_`` methods at the right places (described in docstrings):

    .. code ::

       ...
       # receiving and processing the issue
       supervisor.report_issue(issue)
       # additional work with the issue
       ...

    Your implementation may add custom callbacks:

    .. code ::

       def my_procedure(issue):
           ...

       supervisor.callbacks['issue'].append(my_procedure)
       # my_procedure will be called when report_issue is
       # called on the supervisor object

    You may also use ``supervisor.obj`` for your data as you
    need. Do not touch other parameters nor edit this class!

    :ivar api_endpoint: API endpoint to be used for communication
    :ivar token: API token to be used (you can use ``has_token``)
    :ivar wait_rate_limit:
        True if the app should wait until the rate limit resets after it is
        exceeded, False if exceeding the limit should cause
        :exc:`~asya.exceptions.AsyaException`
    :ivar skip_404:
        True the app should skip 404 errors, False if they should
        raise :exc:`~asya.exceptions.AsyaException`
    :ivar per_page: size of page for API requests
    """

    def __init__(self, api_endpoint, token, wait_rate_limit, skip_404,
                 per_page=100):
        self.api_endpoint = api_endpoint
        self.token = token
        self.wait_rate_limit = wait_rate_limit
        self.skip_404 = skip_404
        self.per_page = per_page
        self.data = {}
        self.callbacks = defaultdict(list)
        self.obj = None  #: User obj (can be anything)

    @property
    def has_token(self):
        """True if the API token is set"""
        return self.token is not None

    def report_issues_search_page(self, page, number):
        """
        Method to be called before processing of a single result page

        :param page: page of issues search (data from API)
        :type page: dict
        :param number: number of the page
        :type number: int
        """
        self._do_callback('issues_search_page', page, number)

    def report_issue(self, issue):
        """
        Method to be called after processing of a single issue

        :param issue: GitHub issue (data from API)
        :type issue: dict
        """
        self._do_callback('issue', issue)

    def report_comment(self, comment):
        """
        Method to be called after processing of a single comment

        :param comment: GitHub comment (data from API)
        :type comment: dict
        """
        self._do_callback('comment', comment)

    def report_wait(self, active, headers):
        """
        Method to be called whenever changing waiting state
        (see ``wait_rate_limit``)

        :param active: True if wait is starting, False if ending
        :type active: bool
        :param headers: headers of the API response that caused waiting
        :type headers: dict
        """
        self._do_callback('wait', active, headers)

    def report_skip(self, headers):
        """
        Method to be called whenever some result is skipped
        (see ``skip_404``)

        :param headers: headers of the API response that caused skipping
        :type headers: dict
        """
        if not self.skip_404:
            raise PermissionError('Not allowed to skip anything!')
        self._do_callback('skip', headers)

    def _do_callback(self, callback_name, *args, **kwargs):
        for call in self.callbacks[callback_name]:
            call(*args, **kwargs)

    def __getattr__(self, item):
        if item.startswith('report_'):
            callback_name = item[7:]

            def callback(*args, **kwargs):
                return self._do_callback(callback_name, *args, **kwargs)
            return callback

        raise AttributeError(item)
