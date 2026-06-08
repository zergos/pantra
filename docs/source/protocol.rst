Python protocol
===============

Each :doc:`component <components>` can use :ref:`Python script <python tag>` to extend it's own functionality.
Python script is not limited and can use any modules or server resources providing rich backend
event-driven operations.

Local context
-------------

Python code declares component local context with variables' and methods names' accessible inside any component
expression or script. There are some helper variables are predefined:

* `ctx` - dictionary of all local variables, introduced to perform :doc:`reactive <reactive>` writing::

    message: str = "..."

    def action_reactive(node):
        ctx['message'] = "Clicked!"

    def action_silent(node):
        global message
        message = "Clicked!"

* `refs` - dictionary of named :ref:`references <ref>`
* `session` - current :class:`~pantra.session::Session` instance::

    session.log("read me in the console")

* `_` - language :doc:`translation <translation>` function::

    message = _("Hello, {}", user_name)

* `logger` - server-side prepared :class:`logger <logging.Logger>`

All variables above are predefined, but to avoid IDE checker errors, `pantra` provides special "dummy" module
with variables definition `pantra.ctx`::

    from pantra.ctx import *

    message: Property[str] = ""

    def action(node):
        # all variables are imported from `ctx` to suppress error messages
        ctx["message"] = _("hello")
        refs["title"].set_text("foo")
        session.log("bar")
        logger.info("here")

All local variables are exposed to override by component usage, however,
there is also exposed variables explicit annotation convention via `Property` meta-class::

    message: Property[str] = "Hello there!"

Events
------

`pantra` introduces event-driven model, what means each user interaction perform :ref:`event <events>`,
which can run server-side action.

Reserved actions:

* `def init():` - initialize component context before rendering. Basically this method returns nothing, but when
  `False` value is returned - `ContextInitFailed` exception raised preventing component creation.
* `def on_render():` - executes after component rendering to perform final changes
* `def on_restart():` - executes before very first rendering
* `def node_processor(node):` - executes after attributes evaluation before rendering for each node.
  This method makes possible to use custom attributes and tags. Just note possible running slowdown,
  because of calling thi method on each node.
* `action.on_kill` - executes when task is killed by :doc:`scheduler <threads>`::

    def long_running_action(node):
        do_smth_long()

    def long_task_stopped():
        ctx["message"].set_text("Eventually stopped")

    long_running_action.on_kill = long_task_stopped

