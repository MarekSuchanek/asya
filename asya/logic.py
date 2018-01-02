import time

import requests

from .exceptions import AsyaException


class GitHubHeaders:

    def __init__(self, headers):
        self.headers = headers

    def __getitem__(self, key):
        return self.headers.get(key, '')

    @property
    def status_code(self):
        return int(self.headers['Status'][0:3])

    @property
    def ratelimit_exhausted(self):
        return self.status_code == 403 and self.ratelimit_remaining == 0

    @property
    def ratelimit_remaining(self):
        return int(self.headers.get('X-RateLimit-Remaining', -1))

    @property
    def ratelimit_reset(self):
        return int(self.headers.get('X-RateLimit-Reset', -1))

    @property
    def ratelimit_wait(self):
        return max(0, self.ratelimit_reset - int(time.time()))


def prepare_session(supervisor, default_session=None):
    session = default_session or requests.Session()
    if not supervisor.has_token:
        return session

    def github_token_auth(req):
        req.headers['Authorization'] = 'token ' + supervisor.token
        return req

    session.auth = github_token_auth
    return session


def api_fetch(supervisor, url, params, expected_code=200):
    response = supervisor.obj['session'].get(url, params=params)

    gheaders = GitHubHeaders(response.headers)
    if gheaders.status_code != expected_code:
        if gheaders.status_code == 404 and supervisor.skip_404:
            supervisor.report_skip(response.headers)
            return None

        if gheaders.ratelimit_exhausted and supervisor.wait_rate_limit:
            supervisor.report_wait(True, response.headers)
            time.sleep(gheaders.ratelimit_wait)
            supervisor.report_wait(False, response.headers)
            return api_fetch(supervisor, url, params)

        raise AsyaException(response.json(), response.headers)
    return response


def api_results(supervisor, url, params):
    response = api_fetch(supervisor, url, params)
    if response is not None:
        yield response.json()
    while 'next' in response.links:
        url = response.links['next']['url']
        response = api_fetch(supervisor, url, params)
        if response is not None:
            yield response.json()


def gather_acquaintances(search_specs, supervisor):
    """Gather acquaintances from GitHub issues and comments with
    given search_specs with counts of comments in form of dict.
    It uses :mod:`asyncio` and :class:`aiohttp.ClientSession`.

    >>> gather_acquaintances({'q': 'author:MarekSuchanek'}, supervisor)
    {'MarekSuchanek': 7, 'hroncok': 15, 'encukou': 10}

    For more information about the ``search_specs`` content visit the
    `GitHub Search API docs <https://developer.github.com/v3/search/#search-issues>`_.

    :param search_specs: dictionary with search specification (params for the search)
    :type search_specs: dict
    :param supervisor: supervisor object used for this gathering
    :type supervisor: asya.supervisor.AsyaSupervisor

    :return: dictionary with usernames as keys and number of comments as values
    :rtype: dict
    """
    # return {}
    from collections import defaultdict

    search_specs['per_page'] = supervisor.per_page
    supervisor.obj = dict()
    supervisor.obj['session'] = prepare_session(supervisor)
    supervisor.obj['counts'] = defaultdict(int)

    def add_comment(comment):
        supervisor.obj['counts'][comment['user']['login']] += 1

    supervisor.callbacks['comment'].append(add_comment)

    page = 1
    search_url = supervisor.api_endpoint + '/search/issues'
    params = {'per_page': supervisor.per_page}

    for search_result in api_results(supervisor, search_url, search_specs):
        supervisor.report_issues_search_page(search_result, page)
        for issue in search_result['items']:
            for comments in api_results(supervisor, issue['comments_url'], params):
                for comment in comments:
                    supervisor.report_comment(comment)
            supervisor.report_issue(issue)
        page += 1
    return supervisor.obj['counts']
