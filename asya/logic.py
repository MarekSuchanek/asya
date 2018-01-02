import asyncio
import async_timeout
import time

import aiohttp
import requests
from urllib.parse import urlparse, parse_qs

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


def get_last_page(headers):
    links = requests.utils.parse_header_links(headers['Link'])
    links2 = {link['rel']: link['url'] for link in links}
    params = parse_qs(urlparse(links2['last']).query)
    return int(params['page'][0])


async def fetch_data_header(session, url, params=None):
    with async_timeout.timeout(10):
        async with session.get(url, headers=session.headers,
                               params=params) as response:
            return await response.json(), response.headers


async def fetch_and_process(supervisor, session, url, processor, params=None,
                            expected_code=200):
    data, headers = await fetch_data_header(session, url, params)

    gheaders = GitHubHeaders(headers)
    if gheaders.status_code != expected_code:
        if gheaders.status_code == 404 and supervisor.skip_404:
            supervisor.report_skip(headers)
            return None

        if gheaders.ratelimit_exhausted and supervisor.wait_rate_limit:
            supervisor.report_wait(True, headers)
            await asyncio.sleep(gheaders.ratelimit_wait)
            supervisor.report_wait(False, headers)
            return await fetch_and_process(supervisor, session, url,
                                           processor, params, expected_code)

        raise AsyaException(data, headers)
    return await processor(data, headers)


async def process_comment(supervisor, comment):
    supervisor.report_comment(comment)


async def process_pages(session, supervisor, url, params, process_item):
    async def process(data, headers):
        async def process_page(page):
            xparams = {'page': page}
            xparams.update(params)

            async def process_data(data, _):
                futures = [
                    asyncio.ensure_future(process_item(item)) for item in data
                ]
                await asyncio.gather(*futures)

            await fetch_and_process(supervisor, session, url,
                                    process_data, xparams)

        futures = [asyncio.ensure_future(process_item(item)) for item in data]

        if 'Link' in headers:
            last_page = get_last_page(headers)
            for act_page in range(2, last_page + 1):
                futures.append(asyncio.ensure_future(process_page(act_page)))

        await asyncio.gather(*futures)

    await fetch_and_process(supervisor, session, url, process, params)


async def process_issue(session, supervisor, issue):
    async def process(comment):
        await process_comment(supervisor, comment)

    await process_pages(
        session,
        supervisor,
        issue['comments_url'],
        {'per_page': supervisor.per_page},
        process
    )
    supervisor.report_issue(issue)


async def gather_acquaintances_from_issues(search_specs, supervisor):
    url = supervisor.api_endpoint + '/search/issues'
    async with aiohttp.ClientSession() as session:
        session.headers = {'User-Agent': 'Python/ASYA'}
        if supervisor.has_token:
            session.headers['Authorization'] = 'token ' + supervisor.token

        async def process_item(issue):
            await process_issue(session, supervisor, issue)

        async def process_page(data, _, page):
            supervisor.report_issues_search_page(data, page)
            futures = [asyncio.ensure_future(process_item(item))
                       for item in data['items']]
            await asyncio.gather(*futures)

        async def process_query_page(page):
            params = {'page': page}
            params.update(search_specs)

            async def process_data(data, headers):
                await process_page(data, headers, page)

            await fetch_and_process(supervisor, session, url,
                                    process_data, params)

        async def process(data, headers):
            futures = [asyncio.ensure_future(process_page(data, headers, 1))]

            if 'Link' in headers:
                last_page = get_last_page(headers)
                for page in range(2, last_page + 1):
                    futures.append(asyncio.ensure_future(
                        process_query_page(page))
                    )

            await asyncio.gather(*futures)

        await fetch_and_process(supervisor, session, url,
                                process, search_specs)


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

    supervisor.obj = {'counts': defaultdict(int)}

    search_specs['per_page'] = supervisor.per_page

    def add_comment(comment):
        supervisor.obj['counts'][comment['user']['login']] += 1

    supervisor.callbacks['comment'].append(add_comment)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        gather_acquaintances_from_issues(search_specs, supervisor)
    )
    loop.close()

    return supervisor.obj['counts']
