:tocdepth: 2

Reactivity and effects
======================

Modern terms definition:

..  glossary::

    reactive
        In web frameworks, reactivity is the system that automatically updates the webpage (the UI) whenever
        the underlying data (the state) changes.

    imperative
        The opposite model to reactivity is the imperative model (often referred to as manual DOM manipulation
        in web development).

    effects
        In reactive web frameworks, effects (often called useEffect in React or watchEffect in Vue)
        are functions that run automatically when the data they depend on changes. They are used to
        sync your reactive data with systems outside the framework.

Fortunately, `pantra` supports **both** models: reactive and imperative. Second one by default.

..  note::

    Despite imperative model is older at takes more code to manage, it makes logic much more explicitly obvious and
    code running faster, avoiding implicit unwanted effects.

.. highlight:: pantra

Example of imperative logic::

    <div ref:message>Nothing</div>
    <button on:click="action">Click me</button>
    <python>
    def action(node):
        refs['message'].set_text("Hello there!")
    </python>

Let's imaging we want to keep message in local context::

    <div ref:message>{{message}}</div>
    <button on:click="action">Click me</button>
    <python>
    message: str = "Nothing"
    def action(node):
        ctx['message'] = "Hello there!"
        refs['message'].update()
    </python>

And this code could be simplified:

..  code-block::
    :emphasize-lines: 1

    <div>!{{message}}</div>
    <button on:click="action">Click me</button>
    <python>
    message: str = "Nothing"
    def action(node):
        ctx['message'] = "Hello there!"
    </python>

Noticed exclamation mark (`!`) here? It informs engine to watch for `message` variable changes and then
update related node (`<div>` element).

It works the same for attributes expressions

..  code-block::
    :emphasize-lines: 8

    <div style="width: 100vw; height: 100vh;">
        <p on:drag="DragCtrl"
           style="
                width: 50px;
                height: 50px;
                position: absolute;
                background-color: blue;"
           css:left=!{x}
        />
        <button on:click="action">Click me</button>
    </div>
    <python>
    from pantra.ctx import *

    x: int = 0
    def action(node):
        ctx['x'] = WebUnits(100)
    </python>

And for :ref:`conditional <conditions>` nodes:

..  code-block::
    :emphasize-lines: 1

    !{{#if mode == "entry"}}
        <input type="text" placeholder="User name" bind:value="user_name">
        <button on:click="action">Enter</button>
    {{#else}}
        <div>Hello, {{user_name}}!</div>
    {{/if}}
    <python>
    mode: str = "entry"
    user_name: str = ""
    def action(node):
        ctx["mode"] = "passed"
    </python>

..  seealso::

    Read more about :ref:`reactive macros <reactive macros>`, :ref:`reactive attribute <reactive attr>`
    and :ref:`reactive tag <reactive tag>`.

..  note::

    Reactive variable names are extracted from the expression using :mod:`ast` parser. It means there is no
    function call tracing for deeper variables changes. As example::

        <div>!{{get_message()}}</div>
        <python>
        message: str = "Hello"
        def get_message():
            return message # <- variable "message" will no be tracked for changes
        </python>

    This was done consciously, to avoid possible mistakes from implicit variable changes tracking and further effects.
    Better practise is to make reactions explicitly:

    ..  code-block::
        :emphasize-lines: 2

        <div ref:message_slot>{{get_message()}}</div>
        <react to="message" action="update:message_slot"/>
        <python>
        message: str = "Hello"
        def get_message():
            return message
        </python>

    Reed more about :ref:`node events <node events>`.

Reactive dictionary
-------------------

..  autoclass:: pantra.components.reactdict::ReactDict
    :members:

