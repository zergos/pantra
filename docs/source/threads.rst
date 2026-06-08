Threading model
===============

As noted in :ref:`dataflow chart <dataflow>` each user action is processed by separate
thread (sync or async depending on function definition). `Pantra` provides flexible control for threads creation and
elimination. Most of logic is :doc:`configurable <configuration>`.

If short words `pantra` allocate `MIN_TASK_THREADS` threads in advance to handle average traffic.
After available threads shortage `pantra` creates new threads until `MAX_TASK_THREADS` count reached,
and after that, when traffic getting low, it kills redundant threads.

It is also takes care about hanged threads and passive sessions.

.. graphviz:: charts/threads_chart.dot

..  seealso::

    Check method source code :meth:`~pantra.workers.base.BaseWorkerServer.tasks_controller()`
