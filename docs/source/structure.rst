Directory structure
===================

*Pantra* checks for directories relative to project path by default.

..  note::

    Most of directories could be redeclared via :doc:`configuration <configuration>`

Structure details:
 * `apps` directory contains one or more applications
 * :doc:`Configuration <configuration>` file in `apps\\config.py`
 * `components` directory contains raw :doc:`components <components>`
 * `css` directory - common CSS/SCSS files
 * `cached` directory is created by :doc:`cache builder <cache>`

Directories::

    project
    ├── apps                         -- user applications base path,
    │   ├── app1                          subdirectory name -> app name -> HTTP relative path
    │   ├── app2                          app2 -> http://localhost:8005/app2
    │   │   ├── static               -- app static files base path (images, fonts, etc.)
    │   │   │   ├── 1.jpg                 <img src:static="1.jpg">
    │   │   │   ├── 2.jpg
    │   │   │   └── photos           -- static subdirectory
    |   │   │       └── me.png            <img src:photos="me.png">
    │   │   ├── storage              -- session storage to store user settings
    │   │   │   ├── common.dat            ShelveDB adapter for this example
    │   │   │   └── common.dir
    │   │   ├── data                 -- database schema
    │   │   │   ├── __init__.py      -- `quazydb` tables
    │   │   │   ├── __init__.pyi     -- developer-friendly tables
    │   │   │   └── databases.xml    -- DB connection details
    │   │   ├── locale               -- Babel i18n language files
    │   │   │   ├── ru_RU
    │   │   │   └── zh_CN
    │   │   ├── Comp1.html           -- any custom components related to app
    │   │   ├── Comp2.html
    │   │   └── Main.html            -- Main (starting) component of app
    │   └── config.py                -- custom engine configuration
    ├── css                          -- common SCSS/CSS files
    │   ├── basic.scss                    compatible with @import directive
    │   ├── common.scss                   <style type="text/scss">
    │   ├── defaults.scss                   @import "css/defaults";
    │   └── ...                             pre { color: $color-decoration; }
    ├── components                   -- comon components directory
    │   ├── Dialogs
    │   ├── Forms
    │   │   ├── Button.html
    │   │   ├── RadioBox.html
    │   │   ├── SelectBox.html
    │   │   └── ...
    │   ├── Layout
    │   ├── ...
    │   ├── helpers                  -- common scripts for components
    │   │   ├── dialogs.py
    │   │   ├── layout.py
    │   │   ├── widgets.py
    │   │   └── ...
    │   ├── locale                   -- Babel i18n language files
    │   │   ├── ru_RU
    │   │   └── zh_CN
    │   ├── static                   -- common static files
    │   │   ├── icons
    │   │   └── images
    │   ├── bootstrap.html           -- main startup template
    │   └── html5.dtd                -- modified DTD schema for development purpose
    └── cached                       -- generated cache directory
        ├── apps
        ├── core
        ├── css
        ├── helpers
        ├── js
        ├── static
        └── bootstrap.html
