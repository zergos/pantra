Static files
============

`pantra` provides advanced ways to provide links to your static and media files.
Additionally to plain `href` and `src` attributes `pantra` provides localized versions:

* `href:subdir`
* `src:subdir`

It helps to rendering engines to find proper file in specific sub-directory name, relatively to current app and
component. Since then, rendering engine has multi-step searching algorith:

#. Search in subdirectory `ALLOWED_DIRS` :doc:`aliases <configuration>`
#. Search in app subdirectory `/app/app_name/static/subdir/`
#. Search in component subdirectory `/component_path/static/subdir/`
#. Search on common components subdirectory `/components/static/subdir/`

..  seealso::

    Check common directory :doc:`structure <structure>`.

..  important::

    If `subdir` equals "static", search is performing in `static` directory instead of `subdir`::

    <img src:media="image.png">   <-- .../static/media/image.png
    <img src:static="image.png">  <-- .../static/image.png

..  note::

    All static files to be collected to single directory on :doc:`cache building <cache>` process.
