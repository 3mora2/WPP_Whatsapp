import asyncio

# from threading import Thread, Event
#
#
# def setInterval(func, interval, *args, **kwargs):
#     stopped = Event()
#
#     async def loop():
#         while not stopped.wait(interval):
#             await func(*args)
#
#     Thread(target=loop).start()
#     return stopped


# def setInterval(func, interval, *args, **kwargs):
#     stopped = asyncio.Event()
#     loop = kwargs.get('loop') or asyncio.get_event_loop()
#
#     async def loop_():
#         print("__nn__")
#         while not stopped.is_set():
#             await func()
#             await asyncio.sleep(interval)
#
#     loop.create_task(loop_())
#     return stopped



# async def pprint_():
#     print("ffffffffffffff")
#
#
# d = setInterval(pprint_, 5)
#
# async def asetInterval(func, timeout, *args):
#     print("setInterval")
#     while True:
#         await asyncio.sleep(timeout / 1000)
#         print("func")
#         await func(*args)
#
#
# def setTimeout(func, time, *args):
#     stopped = Event()
#
#     def loop():
#         while not stopped.wait((time / 1000)):
#             func(*args)
#             stopped.set()
#
#     Thread(target=loop).start()
#     return stopped
#
#
# def clearInterval(Interval):
#     try:
#         if Interval:
#             Interval.stop()
#             print("Interval", Interval.cancelled())
#             # Interval.clear()
#     except:
#         traceback.print_exc()


from typing import Dict


class EventEmitter:

    def __init__(self):
        self._callbacks: Dict[str, callable] = {}

    def on(self, event_name, function):
        self._callbacks[event_name] = self._callbacks.get(event_name, []) + [function]
        return function

    def emit(self, event_name, *args, **kwargs):
        [function(*args, **kwargs) for function in self._callbacks.get(event_name, [])]

    def off(self, event_name, function):
        self._callbacks.get(event_name, []).remove(function)
