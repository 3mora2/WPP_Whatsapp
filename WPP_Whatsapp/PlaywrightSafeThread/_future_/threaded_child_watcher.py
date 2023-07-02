# from: https://github.com/python/cpython/blob/3.8/Lib/asyncio/unix_events.py
import os
import itertools
import threading
import warnings
from asyncio import get_running_loop
from asyncio.log import logger


def _compute_returncode(status):
    if os.WIFSIGNALED(status):
        # The child process died because of a signal.
        return -os.WTERMSIG(status)
    elif os.WIFEXITED(status):
        # The child process exited (e.g sys.exit()).
        return os.WEXITSTATUS(status)
    else:
        # The child exited, but we don't understand its status.
        # This shouldn't happen, but if it does, let's just
        # return that status; perhaps that helps debug it.
        return status


class AbstractChildWatcher:
    """Abstract base class for monitoring child processes.

    Objects derived from this class monitor a collection of subprocesses and
    report their termination or interruption by a signal.

    New callbacks are registered with .add_child_handler(). Starting a new
    process must be done within a 'with' block to allow the watcher to suspend
    its activity until the new process if fully registered (this is needed to
    prevent a race condition in some implementations).

    Example:
        with watcher:
            proc = subprocess.Popen("sleep 1")
            watcher.add_child_handler(proc.pid, callback)

    Notes:
        Implementations of this class must be thread-safe.

        Since child watcher objects may catch the SIGCHLD signal and call
        waitpid(-1), there should be only one active object per process.
    """

    def add_child_handler(self, pid, callback, *args):
        """Register a new child handler.

        Arrange for callback(pid, returncode, *args) to be called when
        process 'pid' terminates. Specifying another callback for the same
        process replaces the previous handler.

        Note: callback() must be thread-safe.
        """
        raise NotImplementedError()

    def remove_child_handler(self, pid):
        """Removes the handler for process 'pid'.

        The function returns True if the handler was successfully removed,
        False if there was nothing to remove."""

        raise NotImplementedError()

    def attach_loop(self, loop):
        """Attach the watcher to an event loop.

        If the watcher was previously attached to an event loop, then it is
        first detached before attaching to the new loop.

        Note: loop may be None.
        """
        raise NotImplementedError()

    def close(self):
        """Close the watcher.

        This must be called to make sure that any underlying resource is freed.
        """
        raise NotImplementedError()

    def is_active(self):
        """Return ``True`` if the watcher is active and is used by the event loop.

        Return True if the watcher is installed and ready to handle process exit
        notifications.

        """
        raise NotImplementedError()

    def __enter__(self):
        """Enter the watcher's context and allow starting new processes

        This function must return self"""
        raise NotImplementedError()

    def __exit__(self, a, b, c):
        """Exit the watcher's context"""
        raise NotImplementedError()


class ThreadedChildWatcher(AbstractChildWatcher):
    """Threaded child watcher implementation.

    The watcher uses a thread per process
    for waiting for the process finish.

    It doesn't require subscription on POSIX signal
    but a thread creation is not free.

    The watcher has O(1) complexity, its performance doesn't depend
    on amount of spawn processes.
    """

    def __init__(self):
        self._pid_counter = itertools.count(0)
        self._threads = {}

    def is_active(self):
        return True

    def close(self):
        self._join_threads()

    def _join_threads(self):
        """Internal: Join all non-daemon threads"""
        threads = [
            thread
            for thread in list(self._threads.values())
            if thread.is_alive() and not thread.daemon
        ]
        for thread in threads:
            thread.join()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __del__(self, _warn=warnings.warn):
        threads = [
            thread for thread in list(self._threads.values()) if thread.is_alive()
        ]
        if threads:
            _warn(
                f"{self.__class__} has registered but not finished child processes",
                ResourceWarning,
                source=self,
            )

    def add_child_handler(self, pid, callback, *args):
        loop = get_running_loop()
        thread = threading.Thread(
            target=self._do_waitpid,
            name=f"waitpid-{next(self._pid_counter)}",
            args=(loop, pid, callback, args),
            daemon=True,
        )
        self._threads[pid] = thread
        thread.start()

    def remove_child_handler(self, pid):
        # asyncio never calls remove_child_handler() !!!
        # The method is no-op but is implemented because
        # abstract base classe requires it
        return True

    def attach_loop(self, loop):
        pass

    def _do_waitpid(self, loop, expected_pid, callback, args):
        assert expected_pid > 0

        try:
            pid, status = os.waitpid(expected_pid, 0)
        except ChildProcessError:
            # The child process is already reaped
            # (may happen if waitpid() is called elsewhere).
            pid = expected_pid
            returncode = 255
            logger.warning(
                "Unknown child process pid %d, will report returncode 255", pid
            )
        else:
            returncode = _compute_returncode(status)
            if loop.get_debug():
                logger.debug(
                    "process %s exited with returncode %s", expected_pid, returncode
                )

        if loop.is_closed():
            logger.warning("Loop %r that handles pid %r is closed", loop, pid)
        else:
            loop.call_soon_threadsafe(callback, pid, returncode, *args)

        self._threads.pop(expected_pid)
