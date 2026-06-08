:tocdepth: 2

Configuration
=============

Config file
-----------

.. highlight:: python

Configuration file is located in `apps/config.py`. Also, additional parameters could be provided via environment
variables with prefix `PANTRA_`.

There are two ways to declare parameters in `config.py`:

#. As global variable (old style)::

    MIN_TASK_THREADS = 1
    MAX_TASK_THREADS = 2

#. As `AppConfig` subclass attributes (recommended)::

    from pantra.defaults import Config

    class AppConfig(Config):
        MIN_TASK_THREADS = 1
        MAX_TASK_THREADS = 2

Environment variables
---------------------

`pantra` also reads environment variables, prefixed with `PANTRA_`. There is value parsing convention to detect types:

* `1234` - anything starting with a digit -> is a number
* `True` or `False` -> is a boolean value
* `None` -> literally `None`
* Any other value is a string

..  code-block:: bash

    PANTRA_MIN_TASK_THREADS=1
    PANTRA_MAX_TASK_THREADS=2
    pantra run

Parameters list
---------------

..  autoclass:: pantra.defaults::Config
    :members:

Config API
----------

To access parameters in a code use two global variables:

* `safe_config` - contains constant values only, which is possible to evaluate literally (without calls).
  It is safe to use on start time. to avoid modules import recursion::

    from pantra.settings import safe_config

    if safe_config.PRODUCTION:
        print("Early stage initialization")

* `config`- contains all evaluated (later) parameters::

    from pantra.settings import config

    print(config.DEFAULT_APP)

