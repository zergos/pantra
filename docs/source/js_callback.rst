JavaScript callback
===================

Client to server
----------------

To call backend from JavaScript `pantra` defines method: `processCall(oid, func_name, *args)`. Called function
should be allowed by :meth:`~pantra.components.context.Context.allow_call`.

* `oid` - is unique node OID of any node in execution context. There is simple JS API to get OID:

  * `OID.get(node)` - get node OID
  * `OID.node(oid)` - get node by OID

  Otherwise, get node ID with pythonic expression `node.oid`.

* 'func_name` - function defined in local Python script
* `args` - all simple types are serializable including lists and dicts

Example:

..  code-block:: pantra

    <script type="text/javascript" >
    function go(oid) {
        let data = {
            a: 1,
            b: 2,
            c: 3
        };

        processCall(oid, "call_from_client", data);
    }
    </script>
    <button onclick="go(`{ctx.oid}`)">Call from client</button>
    <python>
    def init():
        ctx.allow_call('call_from_client')

    def call_from_client(data):
        session.log(data)
    </python>

Server to client
----------------

To call JavaScript method from Python script use :meth:`~pantra.session.Session.call` method.
All simple types are serializable including lists and dicts.

Example:

..  code-block:: pantra

    <script type="text/javascript">
        function callFromServer(data) {
            console.log(data);
        }
    </script>
    <button on:click="go">Call from server</button>
    <python>
    def go(node):
        data = {
            'hello': 'from server',
        }
        session.call("callFromServer", data)
    </python>
