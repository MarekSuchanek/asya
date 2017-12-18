

def gather_acquaintances(search_specs, supervisor):
    """Gather acquaintances from GitHub issues and comments with
    given search_specs.
    Return a dict mapping usernames to numbers of comments.

    Uses :mod:`asyncio` and :class:`aiohttp.ClientSession`.

    >>> gather_acquaintances({'q': 'author:MarekSuchanek'}, supervisor)
    {'MarekSuchanek': 7, 'hroncok': 15, 'encukou': 10}

    For more information about the ``search_specs`` content visit the
    `GitHub Search API docs <https://developer.github.com/v3/search/#search-issues>`_.

    This function may not be called while the asyncio event loop is running.
    It starts and stops the event loop automatically.

    :param search_specs: dictionary with search specification (params for the search)
    :type search_specs: dict
    :param supervisor: supervisor object used for this gathering
    :type supervisor: asya.supervisor.AsyaSupervisor

    :return: dictionary with usernames as keys and number of comments as values
    :rtype: dict
    """
    ...
