Database and ORM
================

`pantra` is not bound to any ORM or database engine and works without any database needed. However, specifically
to flexible web framework needs I was designed QuazyDB_ ORM.
This section contains step-to-step guide to install connection to Postgres with QuazyDB_.

.. _QuazyDB: https://quazydb.readthedocs.io/en/stable

Installation
------------

QuazyDB_ is not included in general package, but it could be installed as optional package:

..  code-block:: bash

    $ pip install pantra[quazydb,psycopg]

..  note::

    `psycopg <https://www.psycopg.org/>`__ is also required to connect to Postgres database.

Optionally, prepare empty database on Postgres:

..  code-block:: sql

    CREATE USER pantra WITH PASSWORD 'pantra';
    CREATE DATABASE pantra WITH OWNER pantra;

Then create `apps/system/data/databases.xml`:

..  code-block:: xml
    :caption: databases.xml

    <databases>
        <postgres name="db" schema="system" conninfo="postgresql://pantra:pantra@localhost/pantra"/>
    </databases>

System schema
-------------

Put several meta tables to test:

..  collapse:: Click here to expand/collapse code

    ..  literalinclude:: ../../apps/system/data/__init__.py
        :language: python
        :caption: apps/system/data/__init__.py

It is also recommended to generate stub file: `apps/system/data/__init__.pyi`:

..  code-block:: bash

    $ pantra database.stub system

Then activate migrations:

..  code-block:: bash

    $ pantra database.migration.activate system

Application schema
------------------

Put several files to run simple database application.

..  literalinclude:: ../../apps/storage/data/databases.xml
    :language: xml
    :caption: apps/storage/data/database.xml

..  collapse:: Click here to expand/collapse code

    ..  literalinclude:: ../../apps/storage/data/__init__.py
        :language: python
        :caption: apps/storage/data/__init__.py

..  collapse:: Click here to expand/collapse code

    ..  literalinclude:: ../../apps/storage/Main.html
        :language: pantra
        :caption: apps/storage/Main.html

Then apply migrations and create tables:

..  code-block:: bash

    $ pantra database.migration.apply storage

That's it. Ready to run::

    $ pantra run

Open your browser and enter URL http://localhost:8005/storage

