Manage session tasks
====================

Each function called by the action is running in allocated :doc:`thread <threads>` and wrapped as **session task**.
Each running tasks is identified as context OID plus function name.
There is simple method to stop long running task by name:
:meth:`~pantra.components.render.render_node::RenderNode.kill_task`. To stop all running tasks within a context use
:meth:`~pantra.components.render.render_node::RenderNode.kill_all_tasks`.

Example:

..  code-block:: pantra

    <button on:click="long_job">Start long task</button>
    <button on:click="stop">Stop task</button>
    <div ref:progress/>
    <python>
    import time

    def long_job(node):
        refs["progress"].set_text("In progress...")
        session.send_shot()
        time.sleep(30)
        refs["progress"].set_text("Done")

    def on_kill():
        refs["progress"].set_text("Stopped")
    long_job.on_kill = on_kill

    def stop(node):
        ctx.kill_task(long_job)
    </python>
