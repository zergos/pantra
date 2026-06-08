:tocdepth: 2

Session storage
###############

Bindings
========

Sometimes it is useful to save some of user states between sessions:

* Form values
* Table sort orders
* Visual design options
* Last opened page
* Etc

`pantra` introduces session storage:

..  graphviz::

    digraph "Session storage" {
      size="4,4";
      UI [label="UI data\nor local state"];
      Dict [label="Data mapping\n+key", shape=rect];
      Rec [label="Named\nbinding", shape=rect]
      Storage;
      UI -> Dict -> Rec -> Storage [dir=both];
    }

Classes
=======

Default implementation is set by parameter `

..  autoclass:: pantra.session_storage::SessionStorage
    :members:

..  autoclass:: pantra.session_storage::NullSessionStorage

..  autoclass:: pantra.session_storage::ShelveSessionStorage

