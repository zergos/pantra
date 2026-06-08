Components
==========

Structure
---------

Each component is a valid HTML code. By simple words it consist of nested blocks with text and media content.

Sections (optional):

#. Client-side Java Scripts.
#. Main component HTML markup.
#. Local and global styles.
#. Server-side Python code.

..  highlight:: pantra

Sample code::

    <p ref:greetz>Any HTML code here</p>
    <button on:click="action">Push me!</button>
    <style>
       /* any local style here */
       p { color: green; }
    </style>
    <python>
    # server-side python code
    from pantra.ctx import *
    def action(node):
        refs['greetz'].set_text('Very well!')
    </python>

Each component is stored to a file with extension `html`. Components are semantically grouped by directories,
but component names should be unique. First letter of component name should be in **uppercase**.

Common components are stored in `components` directory. Other components specific to application stored in
application :doc:`directory <structure>`.

Tags and attributes
-------------------

HTML tag
^^^^^^^^

Any regular HTML tag from HTML5 specification is allowed. Tags should be specified in **lowercase**.

..  note::

    First letter case is important. So, `<button>` is treated as HTML tag, but `<Button>` is a component.

Special attributes:

..  _ref:

* `ref:name` - set named reference to this tag to use from code::

    <p ref:message>Listen up</p>
    <python>
    refs['message'].set_text("Hello")
    </python>

* `on:render="func_name"` - calls specified function name after block render::

    <div on:render="say_hi">
        <p ref:message />
    </div>
    <python>
    def say_hi():
        refs['message'].set_text("Hi")
    </python>

* `on:init="func_name"` - calls specified function name before block render::

    <p on:init="prepare">
        <p>{{message}}</p>
    </p>
    <python>
    def prepare():
        ctx['message'] = "Hi"
    </python>

.. _node events:

* HTML events in format `on:event_name="modifier:name"`. Event attributes equals to
  `HTML event <https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model/Events>`_ names:
  `on_click`, `on:change`, etc. Several actions could be separated by space. Modifier options:

  * omitted: `name` - function name. Function has to be declared with argument `node`,
    which filled with reference to fired node::

        <p on:click="say_hi">Click me</p>
        <python>
        def say_hi(node):
            node.set_text('Thank you')
        </python>

  * `update`: `name` - is node referenced name. This node will be updates (with all dynamic attributes)::

        <p ref:message_slot on:click="change_message update:message_slot">{{message}}</p>
        <python>
        message: str = "Click me!"
        def change_message(node):
            global message
            message = "Thank you!"
        </python>

  * `scope`: `name` - is key in scope::

        {{#set:scope action=do_smth}}
        <button on:click="scope:action">Click me!</button>

* `on:drag="DragClass"` - drag-and-drop event. `pantra` provides special class :class:`~pantra.components.controllers.DragController` for this case::

    <div style="width: 100vw; height: 100vh;">
        <p on:drag="DragCtrl"
           style="
                width: 50px;
                height: 50px;
                position: absolute;
                background-color: blue;"
        />
    </div>
    <python>
    from pantra.ctx import *
    from pantra.components.controllers import DragController

    class DragCtrl(DragController):
        node: HTMLElement

        def start(self, node) -> bool:
            if isinstance(node.style, str):
                node.style = DynamicStyles(node.style)
                node.style['left'] = node.metrics.left
                node.style['top'] = node.metrics.top
            self.node = node
            return True

        def move(self):
            self.node.move_box(self.delta_x, self.delta_y)

        def stop(self):
            pass
    </python>

* `on:keyup` and `on:keydown` can track any key pressed. However, it is possible to specify a key name in form
  `on:keydown:Enter`. Check key names on
  `MDN <https://developer.mozilla.org/en-US/docs/Web/API/UI_Events/Keyboard_event_key_values>`__.
  For global events see :ref:`events`::

    <input type="text" on:keyup:Escape="undo_edit">
    <python>
    def undo_edit(node, key):
        node.set_text("")
    </python>

* Class switch `class:name="value"`. Enable or disable class of HTML element by result of expression from value.
  If value is omitted, it means contextual variable name has the same name as class, for example,
  `class:wide` <-> `class:wide="@wide"`. It is possible to combine several class switches with
  regular `class` attribute::

    <div class:hidden="{not visible}"/>

.. _style attr:

* Partial dynamic style `css:style_name="value"`. Assign expression to evaluate specific style. It is possible to omit
  expression when local context has the same variable name: `css:color` <-> `css:color="@color"`. It is impossible to
  combine with regular `style` attribute.::

    <div class="cap" css:width="@caption_width">{{caption}}</div>

* Behavior of boolean attributes is slightly changed: empty strings now are treated as `False`,
  removing attribute at render time. Actual for `checked`, `disabled` and `required`.
* Non-string attribute assigning short form `set:attr_name="value"`.

 * Works better with boolean attributes: `set:hidden="{not visible}"` <-> `hidden="{not visible and 'hidden' else ''}"`
 * Omit value to assign variable with the same name: `set:required` <-> `set:required="{required}"`
 * Works with "focused" state of element: `set:focused` -> sets element focus after render
 * It understands string representation of boolean values: "yes"/"no": `set:focused="yes"` <-> `set:focused="{True}"`::

    <input
            set:id
            set:name
            set:type
            bind:value
            set:placeholder
            set:required
            set:disabled="@readonly"
            css:width
            spellcheck = "{spellcheck and '' or 'false'}"
    >

* Server-to-client variable connector `bind:value`. Works for interactive elements like `<input>`, `<textarea>`,
  `<select>`, etc.

 * It sets initial element value from specified local variable name `bind:value="var_name"`
 * If variable name is omitted, it uses variable with name `value`
 * When user changes value on Web form, server gets new value instantly and assign to variable name.
 * And vice versa: when variable value changed on the server -> it renders on client side instantly::

    <input
        type="{type}"
        set:focused="yes"
        bind:value
        on:focusout="exit_cell"
        on:keyup:Enter="exit_cell"
        on:keyup:Escape="undo_edit"
    >

* `data:name="value"` - store additional data to node context::

    {{#for user in users_list }}
        <p data:user_data="{user.data}" on:click="select_user">{{user.name}}</p>
    {{/for}}
    <python>
    def select_user(node):
        session.log(node.data['user_data'])
    </python>

* `src:static="path"` and `href:static="path"` - both attributes has syntax to refer to local files.
  Check :doc:`static` for more::

    <img src:media="back.png">

.. _reactive attr:

* `reactive` - makes all other attributes "reactive", which means compliant to value changes.
  Check :doc:`reactive` for more::

    <button
        reactive
        type="button"
        on:click="action"
        class:danger
        class:green
        class:default
        set:disabled
    >

* `not:render` - skip this element, and don't process at all.

..  _scope:

* `scope:name="value"` - make additional data visible to nested context::

    <p scope:username="John">
        <p>Hello {{this.scope['username']}}</p>
    </p>

  It is useful for nested components:

  ..  code-block::
      :caption: Main.html

      <p scope:user_action="@update_profile">
          <ProfileLine caption="preference"/>
          <ProfileLine caption="state"/>
      </p>

  ..  code-block::
      :caption: ProfileLine.html

      <label>{{caption}}
          <input type="text" on:change="on_change">
      </label>
      <python>
      def on_change(node):
          ctx.scope['user_action']()
      </python>

  As an alternative there is :ref:`scope macro <scope macro>`

.. _localize:

* `localize=True` - make date/time values shifted to the browser time zone::

    <input type="time" bind:value localize=True>
    <python>
    from datetime import datetime, time, UTC
    value: time = datetime.now(UTC).time()
    </python>

Component tag
^^^^^^^^^^^^^

HTML tags started with uppercase treated as components. Components are loaded from related file names.
File lookup sequence (check :doc:`directory structure <structure>`):

#. Application base path.
#. Application subdirectories.
#. Common components subdirectories.

First component is always named `Main.html`.

Each component attribute treated as local context attribute value:

..  code-block::
    :caption: Main.html

    <Message text="Hello"/>
    <Message text="World!"/>

..  code-block::
    :caption: Message.html

    <p>{{text}}</p>

Special attributes:

* `ref:name` - named reference, same as :ref:`ref <ref>` for HTML tag
* `cref:name` - named reference to a component context. It gives access to component local members as properties of
  the referenced object::

    <Message ref:msg_node cref:msg_ctx/>
    <python>
    def init():
        refs['msg_node']['text'] = "Hello"
        refs['msg_ctx'].text = "Hello"
    </python>

* `on:init="func_name"` - calls specified function name before component render
* `on:render="func_name"` - calls specified function name after component render
* Boolean attribute assigning short form `set:attr_name="value"`.

 * It understands string representation of boolean values: "yes"/"no": `set:focused="yes"` <-> `set:focused="{True}"`
 * Omit value to set `True`: `set:required` <-> `required="{True}"`

* Set `False` short form `not:attr_name` <-> `attr_name="{False}"`.
* `not:render` - skip this component, and don't process at all
* `scope:name="value"` - make additional data visible to nested context. Read :ref:`scope attr <scope>`.

.. _consume:

* `consume="var_name1,var_name2,..."` - simplify component extension by sharing similar variables.

 * If variable names are set, divided by comma, it renders component filling similar variables values:
   `consume="var_name1,var_name2,..."` <-> `"var_name1="{var_name1}" var_name2="{var_name2}" ...`.
   To transmit all local members use `consume="*"`.
 * If variable names list is omitted, consumed component exposes it's own context as initial local then mixed with
   new defined local context.

..  code-block::
    :caption: InputField.html

    <input
            set:id
            set:name
            set:type
            bind:value
            set:placeholder
            set:required
    >

..  code-block::
    :caption: InputPassword.html

    <InputField consume type="password"/>

HTML attribute values
^^^^^^^^^^^^^^^^^^^^^

Additionally to standard HTML attribute values notation via double quotes `"`, `pantra` allows several additional ways:

#. Standard notation `<tag attr="value">`
#. Alternative quotes `<tag attr='value'>`
#. Another alternative quotes `<tag attr=\`value\`>`
#. Numeric value (no quotes) `<Tag int=123 float=1e6>`. Useful for components usage.
#. Boolean value `<tag flag1=True flag2=False>`
#. :ref:`Expressions <expressions>` (also, no quotes):

 * `<tag dynamic={get_value()}>`
 * `<tag react=!{"Hello"+user_name}>`
 * `<tag attr=@var_name>`
 * `<tag attr=!@var_name>`

..  note::

    There is no preferable way and it is still possible to use standard notation only. Despite it overhead, it
    is supported by most of :doc:`IDEs <ide>`, including your favorite one.

Java scripts
^^^^^^^^^^^^

It is possible to insert `<script>` into components, choosing one of two modes:

#. Insert into `<head>` once and reuse for each instance of component. Special attribute `location="head"` or omitted.
   This is default mode. Script to be removed from HEAD when all instances of component are destroyed.
#. Insert into component body as many times as component reached. Special attribute `location="body"`.
   Function and variable names are not isolated between instances, what means, such scripts could include
   runtime logic only.

Example:

..  code-block::
    :caption: MessageButton.html

    <script>
        function showMessage(message) {
            alert(message);
        }
    </script>
    <button onclick="showMessage('{message}')" type="button">Show message</button>
    <script location="body">
        console.log("Message added: {{message}}");
    </script>

..  code-block::
    :caption: Main.html

    <MessageButton message="Hello"/>
    <MessageButton message="World!"/>

It renders like this::

    ...
    <head>
        ...
        <script>
            function showMessage(message) {
                alert(message);
            }
        </script>
    </head>
    <body>
        ...
        <script></script>
        <button type="button" onclick="showMessage('Hello')">Show message</button>
        <script>
            console.log("Message added: Hello");
        </script>
        <script></script>
        <button type="button" onclick="showMessage('World!')">Show message</button>
        <script>
            console.log("Message added: World!");
        </script>
    </body>

..  tip::

    To insert expression in Java Script content use one of two formatters specification: `{{value}}` or `\`{value}\``.

.. _styles:

Styling
^^^^^^^

`pantra` supports `Sassy CSS <https://sass-lang.com/>`__ out of the box::

    <style type="text/scss">
    @import "css/defaults";

    button {
        color: $button-text-color;
        background-color: $button-color-base;

        &:focus, &:hover {
            background-color: darken($button-color-base, 10%);
            border-color: darken($button-color-base, 15%);
            box-shadow: 0 0 0 3px rgba($color-active, .5);
        }
    }
    </style>

..  note::

    Attribute `type="text/scss"` is not necessary, just makes it friendly for some :doc:`IDEs <ide>`.

.. _global selector:

Each style is local, which means, it makes effect within component context only.
To make style explicitly global (affects outside the component context) attribute `global` should be specified.
Or `:global()` pseudo-class for CSS selector.

..  code-block::
    :caption: StyledComponent.html

    <p>Green text locally</p>
    <div>Red text everywhere<div>
    <style>
        p { color: green; }
        :global(div) { color: red; }
    </style>

..  code-block::
    :caption: Main.html

    <div>This text became red</div>
    <StyledComponent/>

It renders like this:

..  code-block:: html
    :caption: app.html

    <div>This text became red</div>
    <p class="StyledComponent">Green text locally</p>
    <div class="StyledComponent">Red text everywhere</div>

..  code-block:: css
    :caption: app.css

    p.StyledComponent {
        color: green
    }
    div {
        color: red
    }

..  note::

    To make localize style effects `pantra` renders component named `class` for each component node
    (`StyledComponent` in example above).

..  note::

    All application-related styles are collected and rendered together
    to a file `<app_name>.local.css`. Read :doc:`template` for more.

..  seealso::

    Some predefined common theme defaults are stored in `css` directory.
    Read more about :doc:`directory structure <structure>`.

..  seealso::

    Also, check individual styling :ref:`features <style attr>`.

.. _python tag:

Python scripts
^^^^^^^^^^^^^^

As you already noticed `pantra` introduces `<python>` tag. Any `Python <https://www.python.org/>`__ code is allowed here.

..  note::

    Python code should be unindented, because of language semantics.

..  hint::

    Python code is always executed first, even, if it is the last block of the content. So, `pantra` makes sure
    all local variables are ready to be rendered on main content.

..  danger::

    It could contain **any** code, indeed, possibly dangerous with unwanted effects. Because Python provides
    an access to almost all system-level operation. Double check your components sources and authors.

Read more at :doc:`protocol`::

    <button on:click="call_event">Push me and read console</button>
    <python>
    def call_event(node):
        session.log("You are the best!")
    </python>

It is possible to load another module in local context namespace using attribute `use="module1,module2,..."`.
Good to use with common properties. Modules should be located at the sme directory as component and had ".py"
extension.

..  code-block::
    :caption: Input.html

    <label class:required class:error="!@error">
        <span>{{caption}}</span>
        <input
            set:required
            bind:value
            set:disabled="@readonly">
            ...
        </input>
    </label>
    <python use="inputs">
    ...
    </python>

..  code-block:: python
    :caption: inputs.py

    from pantra.ctx import *

    caption: Property[str] = ''
    required: Property[bool] = False
    value: Property[str] = ''
    error: Property[str] = ''
    readonly: Property[bool] = False

..  tip::

    The similar effect could be reached if common attributes are defined in abstract component, which then
    :ref:`consumed <consume>`.

.. _events:

Events
^^^^^^

Each HTML node supports server-side events, described :ref:`here <node events>`. Otherwise, it is also possible
to bind events by CSS selector using `<event>` tag with attributes:

* `selector` - `CSS selector <https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Selectors>`__.
  If selector is omitted, event is bound to *root node*. Read :doc:`template` for more.
* `on:event_name="func_name"` - one or many event-to-function bindings
* `global` - don't strict selectors to component's context, similar to :ref:`style <global selector>`.

..  code-block::

    <button>Push 1</button>
    <button>Push 2</button>
    <button>Push 3</button>
    <event selector="button" on:click="do_push"/>
    <python>
    def do_push(node):
        session.log(node.text)
    </python>

Macro codes
-----------

`pantra` introduces mustache-like templating, providing macro-coding within HTML content.

.. _expressions:

Expressions
^^^^^^^^^^^

* Code insertions in attribute values (single brackets):

 * `<tag attr="{expression}">` - evaluate Python expression to make string value.
 * `<tag attr="some text {expression1} some text {expression2}">` - string template with many insertions
 * `<tag attr="js_function(\`{expression}\`)">` - alternative notation: `\`{...}\`` <-> `{...}`
 * `<tag attr="@var_name">` - get value from local context variable
   * `<tag attr=@var_name>` - alternative (no quotes)
 * `<tag attr="#text to be translated">` - value, marked for :doc:`translations <translation>`.
   * <tag attr="#text to be {translated}"> - string template marked for translation
 * `<tag attr="::{precalculated}">` - double-colon marks expression evaluated once (doesn't change on update).

* Code insertions in text content `{{ expression }}` (double quotes). Any Python code is allowed here. Supported one-line
  expression returning string value, including any context variables::

    <p>Good morning, Mr. {{user_name}}.</p>

  Use modifiers in the beginning of text content.

..  note::

    Some modifiers can be combined with each other (in both cases)::

    <div>!#Starting countdown {{counter}}<div>

For each code insertion several variable names are reserved:

* `ctx` - reference to local context (instance of `Context`)
* `refs` - dictionary of named references
* `session` - active user session instance
* `this` - reference to the current rendering node

Read :doc:`scripting protocol <protocol>` for details.

.. _conditions:

Conditional render
^^^^^^^^^^^^^^^^^^

It is possible to render content depending on expression::

    {{#if expression}}
        <div>This is good</div>
    {{#elif alternative}}
        <div>This is also good</div>
    {{#else}}
        <div>This might be good</div>
    {{/if}}

..  warning::

    Conditional macro can not be inserted inside other tags. It should separated solid tags or other macro-blocks only.

Render in loop
^^^^^^^^^^^^^^

Repeat similar part of HTML code in a loop::

    {{#for line in poem}}
        <div>{{line}}</div>
    {{#else}}
        <div>No poem ready yet</div>
    {{/for}}

..  tip::

    Loop syntax doesn't support tuple unpacking yet.

Loops support index function for better caching:

#. When loop block updates - it calculates index function first
#. Then it compare new indices with old ones
#. Then it create blocks with new indices only, removes blocks not matched in the list, and perform order changes.
   It makes sufficient boost for table-based operation, like filtering, sorting and windowing.

..  code-block::

    {{#for row in table # row.id}}
        <tr>
            <td>row.id</td>
            <td>row.data</td>
        </tr>
    {{/for}}

There is special variable name reserved in the loop context: `forloop` object with several attributes:

#. `index` - number of iteration starting from one: 1, 2, 3, ...
#. `index0` - number of iteration starting from zero: 0, 1, 2, ...
#. `parent` - reference to the parent `forloop` object
#. `index` - value of the calculated index

.. _reactive macros:

Reactive
^^^^^^^^

Any content generated by `pantra` is static by default. But it possible to partially
enable :doc:`reactivity <reactive>` using symbol `!` as a prefix before "mustache".

* `<div>!{{dynamic_message}}</div>` - reactive text content
* `<div attr="!{dynamic_expression}">` - reactive attribute value
* `<tag attr="!some text {dynamic_expression}">` - reactive template
* `!{{#if dynamic_condition:}}` - reactive condition
* `!{{#for item in dynamic_list}}` - reactive list (not recommended)

.. _set node:

Set value to variable
^^^^^^^^^^^^^^^^^^^^^

To set new variable to expression use::

    {{#set var_name = expression}}
    ...
    {{/set}}

Close tag for `set` could be omitted.

Supports multiple assignments::

    {{#set
        var_name1 = expression1
        var_name2 = expression2
    }}
    ...
    {{/set}}

When update action is fired all inner content is updated. To rebuild inner content (clear -> build), it is possible to
specify special form `{{#set:clear ...}}`.

.. _scope macro:

Special form sets :ref:`scoped <scope>` variables `{{#set:scope ...}}`.

..  code-block::
    :caption: Main.html

    {{#set:scope action=do_smth}}
        <Control/>
    {{/set:scope}}

..  code-block::
    :caption: Control.html

    <button on:click="scope:action">Click me</button>

.. _reactive tag:

Reactive tag
------------

Additionally to :ref:`reactive macros <reactive macros>` there is a way to bind an action to any variable changes::

    <react to="var_names" action="func_name>
        <!-- block to be updated -->
    </react>

* `var_names` - any variable names in local context, separated by comma
* `func_name` (optional) - calling action (function defined with argument `node` of `ReactNode` type)
* Nested block (optional) will be updated on action

..  code-block::
    :caption: update by function

    <p ref:box>{{get_message()}}</p>
    <react to="message" action="update_message"/>
    <button on:click="change_message">Change message</button>
    <python>
    message: str = "Getting ready"

    def get_message():
        return message

    def update_message(node):
        refs['box'].update(True)

    def change_message(node):
        ctx['message'] = "Changes tracked"
    </python>

..  code-block::
    :caption: update by nested block

    <react to="message">
        <p>{{get_message()}}</p>
    </react>
    <button on:click="change_message">Change message</button>
    <python>
    message: str = "Getting ready"

    def get_message():
        return message

    def change_message(node):
        ctx['message'] = "Changes tracked"
    </python>

Template slots
--------------

Similar to `Web Components <https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_templates_and_slots>`__
`pantra` has "slots" inside components. Is simple words, slots allow to put content inside components.

..  code-block::
    :caption: NumberedList.html

    <ol>
        <slot>
            <li>Empty list</li>
        </slot>
    <ol>

..  code-block::
    :caption: ListItem.html

    <li>{{caption}}</li>

..  code-block::
    :caption: Main.html

    <NumberedList>
        <ListItem caption="Two eggs"/>
        <ListItem caption="One sausage"/>
    </NumberedList>

* Each component can use one unnamed slot (default) and many named.

..  code-block::
    :caption: Product.html

    <div>
        <slot/>
        <slot name="media"/>
        <slot name="description"/>
        <slot name="sources"/>
    <div>

* If no content filled for a component, slot content is generated instead.

    <NumberedList/>

  rendered as::

    <ol>
        <li>Empty list</li>
    <ol>

* To put content inside named slot, special tag `<section>` is introduced::

    <Product>
        <section>
            <p>Top words</p>
        </section>
        <section name="media">
            <img src="123.jpg">
        <section>
        <section name="description">
            <p>Long words</p>
        </section>
    </Product>

* It is possible to extend components keeping slots structure unmodified using `<section>` with attribute `reuse`.

..  code-block::
    :caption: HotProduct.html

    <h1>Hot Hot Hot</h1>
    <Product>
        <section reuse/>
        <section name="media" reuse/>
        <section name="description" reuse/>
        <section name="sources" reuse/>
    </Product>

.. _namespaces:

Non-HTML namespaces
-------------------

`Pantra` supports non-HTML schemas, compatible with any modern browser. Such schemas includes SVG images,
MathML and other special tags listed below.

To describe component as "namespace-specific", it is required to set `ns_type` global variable to
a specific schema number:

..  code-block::
    :caption: SVG.html

    <svg set:width set:height set:viewBox>
        <slot>
            <g font-size="30">
                <text x="20" y="50" color="black">SVG</text>
            </g>
        </slot>
    </svg>

    <python>
    from pantra.ctx import *
    from pantra.imports import NSType

    ns_type = NSType.SVG # <-- here !!!
    width: Property[int] = 1200
    height: Property[int] = 900
    viewBox: Property[str] = ""
    </python>

SVG images
^^^^^^^^^^

Schema: http://www.w3.org/2000/svg

Specification: https://www.w3.org/TR/SVG

Value: `NSType.SVG`

Sample::

    <svg version="1.1" width="5cm" height="5cm">
        <desc>Two groups, each of two rectangles</desc>
        <g id="group1" fill="red">
            <rect x="1cm" y="1cm" width="1cm" height="1cm"/>
            <rect x="3cm" y="1cm" width="1cm" height="1cm"/>
        </g>
        <g id="group2" fill="blue">
            <rect x="1cm" y="3cm" width="1cm" height="1cm"/>
            <rect x="3cm" y="3cm" width="1cm" height="1cm"/>
        </g>

        <!-- Show outline of viewport using 'rect' element -->
        <rect x=".01cm" y=".01cm" width="4.98cm" height="4.98cm"
            fill="none" stroke="blue" stroke-width=".02cm"/>
    </svg>

XML events
^^^^^^^^^^

Schema: http://www.w3.org/2001/xml-events

Specification: https://www.w3.org/TR/xml-events/

Value: `NSType.EVENTS`

Sample::

    <secret ref="/login/password">
        <caption>Please enter your password</caption>
        <info ev:event="help">
            Mail help@example.com in case of problems
        </info>
        <info ev:event="hint">
            A pet's name
        </info>
        <info ev:event="alert">
            This field is required
        </info>
    </secret>

XLink
^^^^^

Schema: http://www.w3.org/1999/xlink

Specification: https://www.w3.org/TR/xlink/

Value: `NSType.XLINK`

Sample::

    <person
    xlink:href="students/patjones62.xml"
    xlink:label="student62"
    xlink:role="http://www.example.com/linkprops/student"
    xlink:title="Pat Jones" />

MathML
^^^^^^

Schema: http://www.w3.org/1998/Math/MathML

Specification: https://www.w3.org/TR/MathML/

Value: `NSType.MATH`

Sample::

    <math display="block">
        <mrow>
          <mi>x</mi>
          <mo>=</mo>
          <mfrac>
            <mrow>
              <mrow>
                <mo>-</mo>
                <mi>b</mi>
              </mrow>
              <mo>&#xB1;</mo>
              <msqrt>
                <mrow>
                  <msup>
                    <mi>b</mi>
                    <mn>2</mn>
                  </msup>
                  <mo>-</mo>
                  <mrow>
                    <mn>4</mn>
                    <mo>&#x2062;</mo>
                    <mi>a</mi>
                    <mo>&#x2062;</mo>
                    <mi>c</mi>
                  </mrow>
                </mrow>
              </msqrt>
            </mrow>
            <mrow>
              <mn>2</mn>
              <mo>&#x2062;</mo>
              <mi>a</mi>
            </mrow>
          </mfrac>
        </mrow>
    </math>

Preserve whitespace
-------------------

`pantra` collapses whitespaces by default the same way as it happens in
`Web Browser <https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Text/Whitespace>`__.

As example:

..  code-block::
    :caption: Component.html

    <div>
        This is             word
                not related
    </div>

It happens stripped after render:

..  code-block::
    :caption: rendered page

    <div>This is word not related</div>

..  note::

    As far as specific CSS property
    `exists <https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/white-space>`__,
    it doesn't affect rendering behavior. The components` content is preliminary rendered by design.

`pantra` tries to preserve whitespaces for text templates:

..  code-block::
    :caption: Component.html

    <div>Hello, dear {{user_name}}!</div>

..  code-block::
    :caption: rendered

    <div>Hello, dear Jinja!</div>

It is also possible to mark content as non-collapsible with cell mark `#` at the end:

..  code-block::
    :caption: Component.html

    <div>
        This is             word
                not related
    #</div>

..  code-block::
    :caption: rendered page

    <div>
        This is             word
                not related
    </div>
