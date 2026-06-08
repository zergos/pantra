:tocdepth: 2

Command line interface
######################

CLI for Python classes
======================

`pantra` uses it's own command line parser, intended to simplify features delivery:

* it exposes direct access to classes methods
* it uses "docstrings" to inspect methods details and info end user
* values directly compatible with Python parser
* it supports common arguments
* extendable model by design

Module description
==================

..  automodule:: pantra.cli4class
    :members:

Pantra commands
===============

The `pantra` CLI is called with this structure:

..  code-include:: :func:`pantra.management.execute_from_command_line`

..  automodule:: pantra.management
    :members:
