Concept and motivation
======================

Engine
------

`pantra` engine specialities:
 #. This is a framework to make Web applications.
 #. Less JavaScript, more Python.
 #. Server-side engine generates and update Web page, client-side just renders and collect user events.
 #. DOM tree of elements is generated on server and then translated to client browser, like remote video game.
 #. Everything is a :doc:`component <components>`. Component is a solid chunk of logic, included in one file:

    * HTML code (using components by choice)
    * styles
    * client-side code
    * server-side code

 #. Single page application. Look-and-feel comparable to regular desktop app.
 #. Multi-tenancy in everything.

    * multiple apps in one
    * multiple users
    * multiple databases
    * multiple locales and languages
    * multiple component packs (to be done)

 #. Support for simple deployment and for complex scaling in compute clouds.

Components
----------

Component definition. Read :doc:`more <components>`.

#. Component is a template.
#. Component is a custom HTML tag.
#. Component is an isolated context with it's own state and logic.
#. Component is a class entity for programmers.
#. Component has unique name and represent a single file.

Action flowchart
----------------

`pantra` represents action-driven logic, which means user interacts with WebUI, triggers events, which send actions
initiating backend workers. Workers change state and DOM (dynamic object model) to be delivered to the user's browser.

..  graphviz:: charts/action_chart.dot

.. _dataflow:

Data flowchart
--------------

The backend consist of two parts:

* Web backend - lightweight workers to process many connections as single entrypoint.
  It maintains web socket connections, gets packet action and
  send to the "compute backend" via :doc:`message queue <message_queue>`.
* Compute backend - heavyweight data processor scaled to a cloud. It unpacks received data from the message queue and
  generates RPC-like request to be called in :doc:`CPU thread <threads>`.
  Then collects DOM changes after call, packs and send back to "web backend".
* Web backend gets back packed DOM changes and send to JavaScript engine in user's browser.

..  graphviz:: charts/data_chart.dot
