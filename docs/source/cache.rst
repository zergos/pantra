Cache builder
=============

Originally `pantra` was designed as interpreter, what means it reads HTML-like files, builds component templates,
and then renders end user nodes brick by brick.

Lately, it was discovered, that it is reasonably to avoid raw files processing at productive deployments.
So, following stages could be performed in advance, by other word, "cached":

#. Parsing HTML-like files by ANTLR4 parser and preparing template nodes.
#. Extracting SCSS code and compiling it to CSS.
#. Building JS minified package of client-side engine.
#. Interpreting template nodes to rendered nodes.

After the deep research it became possible to "convert" original HTML-like files to
Python classes as factories with very least needed code to build specific component.
It takes the best practise of
`"disappearing" frameworks <https://peteroshaughnessy.com/posts/disappearing-frameworks/>`__,
however, approach is slightly different, because it happens server-side, so framework is originally hidden.

In the end, it makes a huge boost to memory consumption and starting lag.

To build a cache there is one CLI command needed::

    $ pantra build_cache <app_name>

It makes `cache` directory (as specified by `CACHE_PATH`) and collect there all needed.
To run the application after caching, choose one of this:

#. Set `RUN_CACHED=True` :doc:`parameter <configuration>` and run normally.
#. Or run with `--cached` flag::

    $ pantra run --cached

..  important::

    It is not necessary to deploy most of the source files after caching, including directories:

    * `css`
    * `components`
    * `apps`

    However, `apps/config.py` should be present (or replaced by env vars).

