Introduction
============

**AS**\ ynchronously-\ **Y**\ our-\ **A**\ cquaintances is simple Python-powered asynchronous
client for GitHub API that allows you to list acquaitances from `GitHub`_ issues = all people
who commented the issues in which is given user involved (author, commenter, assigned, mentioned).
It has of course the ability to filter issues.

How it works
------------

As the name says, it is asynchronous - so all requests are made asynchronously making the tool
quite faster than classic synchronous approach. It uses `asyncio`_ and `aiohttp`_. Task done by
this tool can be sometimes quite complex and reaches a limits of `GitHub API`_. For extending API
rate limit you can provide `personal access token`_ via ``--token``. Nevertheless, it may happen
that you reach limit even with that - you can use ``--wait_rate_limit`` flag and application
will quietly wait until the limit resets (about 1 hour). Other problem is that `GitHub Search API`_
provides only 1000 results so you need to use filter & sort appropriately in some cases.

MI-PYT
------

Task for `MI-PYT`_ course (FIT, CTU in Prague, 2017/18) is to implement the core module of this
application which is :mod:`asya.logic`. Mandatory is to use `asyncio`_, `aiohttp`_ and call
appropriate methods on the ``supervisor`` object of :class:`asya.supervisor.AsyaSupervisor` class.


Installation
------------

You can simply install Asya in standard Python way (system-wide or with virtual env).
Python 3.4 or higher is required (`asyncio`_ is in Python since 3.4).

.. code::

   python setup.py install


Usage
-----

After installation, you can use the CLI of Asya (for more, visit :ref:`CLI docs <cli-docs>`):

.. code::

   asya --help
   asya MarekSuchanek --token <your-secret-API-token>


License
-------

This project is licensed under the MIT License (see the LICENSE file for more details).

.. _GitHub: https://github.com
.. _GitHub API: https://developer.github.com/v3/
.. _GitHub Search API: https://developer.github.com/v3/search/
.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _aiohttp: https://aiohttp.readthedocs.io/en/stable/
.. _personal access token: https://github.com/blog/1509-personal-api-tokens
.. _MI-PYT: https://github.com/cvut/MI-PYT
.. _Marek Suchánek: https://github.com/MarekSuchanek
