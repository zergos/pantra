Translation
===========

`pantra` supports internationalization and localization powered by `Babel <https://babel.pocoo.org/en/latest/>`__

Region and language specification
---------------------------------

`pantra` gets language information from HTTP header, usually filled by Web browser::

    Accept-Language: ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7

Otherwise, `pantra` uses `DEFAULT_LANGUAGE` :doc:`option <configuration>` as fallback language.

What is translated?
-------------------

To perform content translation to different languages this content should be marked by special way.

* Components text content prefixed with #::

    <div>#Hello world!</div>

* String value within `python` code in component with `_` function (alias to :meth:`pantra.session.Session.zgettext`)::

    <div>!{{message}}</div>
    <python>
    message: str
    def action(node):
        ctx['message'] = _("Hello there!")
    </python>

* All database tables names and related attributes names from `app/data/__init__.py`. No special mark needed.

Language files location
-----------------------

Regarding to directory :doc:`structure <structure>` "locales" are located in:

* `apps/app_name/locale/locale_name/LC_MESSAGES/messages.po` - for applications
* `components/locale/locale_name/LC_MESSAGES/messages.po` - for common components

Extract and compile
-------------------

To extract and compile string data use command::

    $ pantra locale.gen

..  seealso::

    Read more about command line :doc:`here <cli>`.
