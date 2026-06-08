:tocdepth: 2

Rendering logic
===============

`pantra` is intended to manipulate DOM tree and content, where each :doc:`component <components>` is
declared in HTML-like text file. This part of magic named is doing by rendering engine, or `renderer`:

#. Locate component related template file.
#. Read and parse it by `ANTLR4 <https://www.antlr.org/>`__ parser.
#. Generate :class:`~pantra.components.template.HTMLTemplate` templates objects tree.
#. Use template objects tree as a factory to render components:

 * Generate specific render nodes
 * Precompile local scripts
 * Run context initializers

#. Update components states on demand.
#. Additionally, renderer controls access to the static and media files, so, it is connected with
   :ref:`routing <routers>`.

..  graphviz:: charts/rendering.dot

Node templates
--------------

..  autoclass:: pantra.components.template::HTMLTemplate
    :members:

..  autoclass:: pantra.components.template::NodeType

..  autoclass:: pantra.components.template::AttrType

..  autoclass:: pantra.components.template::MacroType

..  autoclass:: pantra.components.template::MacroCode

..  autofunction:: pantra.components.template::collect_template

..  autofunction:: pantra.components.template::collect_styles

Rendering model
---------------

..  autoclass:: pantra.components.render.renderer_base::RendererBase
    :members:

There are two builtin renderers:

* :class:`~pantra.components.render.renderer_html.RendererHTML` - to render from HTML-like files
* :class:`~pantra.cached.renderer.RendererCached` - to render from :doc:`cached <cache>` classes

Default renderer is specified by parameter `DEFAULT_RENDERER` in :doc:`configuration <configuration>`.

..  autoclass:: pantra.components.render.renderer_html::RendererHTML

..  autoclass:: pantra.cached.renderer::RendererCached

