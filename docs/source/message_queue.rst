Message queue
=============

This article explains what is message queue on :ref:`data flowchart <dataflow>`.
According to flowchart "web backend" communicates with "compute backend" via message queue.
Actually, any message broker could stand here. So, there are two are bundled at the moment:

#. In-memory queue (default) - simple broker for combined deployment in one joined backend.
#. ZeroMQ adapter - brokerless message queue based on `pyzmq <https://zeromq.org/languages/python/>`__ module.
   Set :doc:`config <configuration>` parameters::

    WORKERS_MODULE = "pantra.workers.zeromq"
    # for network
    ZMQ_LISTEN = 'tcp://*:5555'          # binding IP address:port
    ZMQ_HOST = 'tcp://127.0.0.1:5555'    # IP address:port to connect to
    # for socket piping
    ZMQ_LISTEN = 'ipc:///tmp/pantra.sock'
    ZMQ_HOST = ZMQ_LISTEN

..  hint::

    To adopt another message broker one should inherit :class:`~pantra.workers.base.BaseWorkerServer` and
    :class:`~pantra.workers.base.BaseWorkerClient` classes in one module. Then set `WORKERS_MODULE` to
    this module name.