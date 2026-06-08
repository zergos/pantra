Debugging components
####################

Debugging full stack application could be challenging, because we have to manage code behavior
on the server and on the client (in your browser) same time. This is provided by several tools.

Logging
-------

* Server-side messaging via `logger` :doc:`context <protocol>` variable for server side logging (check it is enable in
  :doc:`configuration <configuration>`).
* Client-side messaging via `session.log` method - sends messages right in the browser's
  `debug console`_.
* All exceptions happened in :doc:`actions' <protocol>` code are also sent to the browser's `debug console`_.
  It also includes last stack trace.

.. _debug console: https://developer.chrome.com/docs/devtools/open

Breakpoints
-----------

..  note::

    Information in this section is very specific to PyCharm IDE and not tested on other IDEs.

To set breakpoint in `pantra` component HTML file there are some steps needed:

#. Enable syntax highlighting of :ref:`Python code <python injections>` (optionally, but recommended).
#. Override current file type to Python (right click on editor tab and select "Override File Type").
#. Set breakpoint on specific line. That's it.
#. To suppress HTML code highlighting as "unsupported" Python code, it is allowed to suppress it with multiline
   comment block.

..  code-block:: python
    :caption: highlighted as python
    :emphasize-lines: 6

    '''
    <div ref:message>Hello there</div>
    <python>
    # '''
    def action(node):
        refs['message'].set_text('foo')
    #</python>

..  code-block:: pantra
    :caption: highlighted as HTML (pantra component)
    :emphasize-lines: 6

    '''
    <div ref:message>Hello there</div>
    <python>
    # '''
    def action(node):
        refs['message'].set_text('foo')
    #</python>

..  important::

    Any initial text of the component outside the node (HTML or Component tag) is ignored, not rendered to a browser.
    So, it could be any textual description including triple quotes mark '''

Stepping exceptions
-------------------

To avoid debug stepping into unwanted service classes, it is also recommended to setup some exceptions::

    File -> Settings -> Build, Execution, Deployment -> Debugger -> Stepping

Set checkbox "Do not step into scripts" and add:

* `enum*`
* `common.py`
* `reactdict.py`

.. _observer:

Observer watchdog
-----------------

It is possible to monitor changes of some files and update them on the fly:

* HTML component source files
* Helpers and database Python source files

There are few step to enable this:

#. Make sure `pantra` not running :doc:`cached <cache>`
#. Make sure `PRODUCTIVE` :doc:`flag <configuration>` is `False`
#. Set `RUN_CACHED` flag to `True`
#. Put restart button to your app:

..  code-block:: pantra

    <button on:click="do_restart">Restart</button>
    <python>
    def do_restart(node):
        session.restart()
    </python>

So that's it. You can run your app, make changes to components and just press button "Restart" after.
No need to restart whole app or browser page.

