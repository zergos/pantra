IDE-friendly tweaks
===================

..  highlight:: none

There is no IDE-related plugin for `pantra` yet, but as an author I usually satisfied with this list of IDE tweaks.

..  note::

    I am editing Python code in PyCharm IDE, so all of my recommendations dedicated to this IDE. Other IDEs need
    different approach. However, who cares in the ages of AI, right?

HTML schema
-----------

`pantra` is bundled with custom `DTD <https://en.wikipedia.org/wiki/Document_type_definition>`__ schema.
It is based on HTML5 and located in `components/html5.dtd`. To configure PyCharm::

    File -> Settings -> Languages & Frameworks -> Schema and DTDs -> External schemas and DTDs -> Add...

It is possible to collect and add to DTD schema all components names:

    $ pantra collect_dtd

Components HTML
---------------

Reduce some HTML inspections::

    File -> Settings -> Editor -> Inspections -> HTML

Disable options:

* Empty tag
* Unknown attribute
* Unknown tag

.. _python injections:

Python injections
-----------------

This is the most important part for component editing! Enable syntax highlighting for Python scripts in HTML code::

    File -> Settings -> Editor -> Language injections -> Add -> XML tag injection

Then set:

* Name = Python scripts
* Language ID = Python
* XML tag -> Local name = python
* OK

..  seealso::

    To debug components read :doc:`here <debug>`.

SCSS support
------------

Make sure your script has type of "text/scss" and SCSS plugin installed to gen pretty highlighted code.

..  code-block:: pantra

    <style type="text/scss">
        @import "css/defaults";
        @import "css/mixins";

        button {
            display: block;
            text-align: center;
            vertical-align: middle;
            border-radius: .25rem;
            margin-top: .5rem;
            margin-bottom: .25rem;
            cursor: pointer;
            color: $button-text-color;
            border: 1px solid darken($button-color-base, 5%);
            background-color: $button-color-base;
            padding: .375rem .75rem;
            @include x-user-select();
            transition: all .15s ease-in-out;

            &:focus, &:hover {
                background-color: darken($button-color-base, 10%);
                border-color: darken($button-color-base, 15%);
                box-shadow: 0 0 0 3px rgba($color-active, .5);
            }

            &.default {
                font-weight: bold;
            }

            &:disabled {
                background-color: grey;
            }
        }
    </style>

Data access
-----------

For the rich code completion to work with :doc:`database <database>` generate stub files::

    $ pantra database.stub

