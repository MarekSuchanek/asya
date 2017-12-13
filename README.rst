asya
====

|license_badge| |rtd_badge|

**AS**\ ynchronously-\ **Y**\ our-\ **A**\ cquaintances from `GitHub`_ issues

Installation
------------

You can simply install Asya in standard Python way (system-wide or with virtual env).
Python 3.4 or higher is required (`asyncio`_ is in Python since 3.4).

.. code::

   python setup.py install


Usage
-----

After installation, you can use the CLI of Asya:

.. code::

   asya --help
   asya MarekSuchanek --token <your-secret-API-token>

Documentation
-------------

Visit `asya.readthedocs.io`_ or after installing Asya, you can also build the documentation on your own:

.. code::

   cd docs
   pip install -r requirements.txt
   make html

Then open ``docs/_build/html/index.html`` in your browser. For more information visit
`Sphinx documentation`_.

License
-------

This project is licensed under the MIT License - see the `LICENSE`_ file for more details.

.. _LICENSE: LICENSE
.. _GitHub: https://github.com
.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _Sphinx documentation: http://www.sphinx-doc.org/en/stable/
.. _asya.readthedocs.io: http://asya.readthedocs.io/en/latest/

.. |license_badge| image:: https://img.shields.io/badge/license-MIT-blue.svg
    :alt: License
    :target: LICENSE

.. |rtd_badge| image:: https://readthedocs.org/projects/asya/badge/?version=latest
    :target: http://asya.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
