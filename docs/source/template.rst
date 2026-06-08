Bootstrap template
==================

`pantra` represents Single Page Web Application (SPA).

Every login is starting from **Main** component, which is putted on **bootstrap** template.
This template collects all styles, `pantra` engine JavaScripts and visual side effects, and prepare
application viewport. It is located in :doc:`components directory <structure>` by default.
Location can be changed by `BOOTSTRAP_FILENAME` :doc:`setting <configuration>`.

#. Initial Web page title.
#. `all.js` - engine's minified JavaScripts (30k)
#. `<body onload="start(...)">` - engine starting point
#. CSS styles:

 * `normalize.css` - simple style normalization (*do I need it?*)
 * `basic.css` - contains `pantra` simple CSS `bootstrap-inspired <https://getbootstrap.com/>`__ framework
 * `global.css` - contains all :ref:`component styles <styles>` for common components
 * `{{app}}.local.css` - contains all styles for app-specific components (binding later)

#. `<div id="display">` - container to load `Main` component and initial content before component is loaded.
#. `<div id="online-bar">` - visual indicator of online status
#. `<svg id="progress-spinner">` - simple SVG animation for busy-status

It uses very limited set of templating features, just allowing several variables inserted with double curve brackets::

    {{VAR_NAME}}

* `APP_TITLE` - :doc:`preconfigured <configuration>` common application title
* `WEB_PATH` - :doc:`preconfigured <configuration>` app domain name (blank by default)
* `INSTANCE_ID` - unique ID generated on app start - can be used for JS and CSS files versioning on development
* `LOCAL_ID` - unique identifier of your session saved in your browser (localStorage)
* `TAB_ID` - unique identifier of your session running in a specific browser tab (sessionStorage)

Sample:

..  code-block:: pantra
    :caption: bootstrap.html

    <!doctype html>
    <html>
    <head>
        <meta charset='utf-8'>
        <meta name='viewport' content='width=device-width'>
        <title>{{APP_TITLE}}</title>
        <script src="{{WEB_PATH}}/js/all.js?{{INSTANCE_ID}}"></script>
        <link rel="stylesheet" href="{{WEB_PATH}}/css/normalize.css?{{INSTANCE_ID}}">
        <link rel="stylesheet" href="{{WEB_PATH}}/css/basic.css?{{INSTANCE_ID}}">
        <link rel="stylesheet" href="{{WEB_PATH}}/css/global.css?{{INSTANCE_ID}}">
        <!--link rel="stylesheet" href="/css/{{app}}.local.css"-->
    </head>

    <body onload="start('{{LOCAL_ID}}', '{{TAB_ID}}', '{{INSTANCE_ID}}', '{{WEB_PATH}}')">
    <div id="online-bar" style="display: none" title="Online"></div>
    <div id="display">
        <div class="init-title">
            <div>Initialization...</div>
        </div>
    </div>

    <svg id="progress-spinner" style="display: none">...</svg>
    </body>
    </html>
