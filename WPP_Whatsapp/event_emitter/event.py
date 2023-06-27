
__all__ = ("EventCallable", "EventHandler", "EventEmitter")

import sys
import threading
import asyncio
import warnings
from typing import Dict, List, Callable, Union, Type


class EventCallable:
    "Callable listener for events"

    def __init__(self, listener: Callable, loop=None):
        if not callable(listener):
            raise TypeError("listener is not callable")
        self._exec_count = 0
        self._original_listener = self._listener = listener
        self._loop = loop
        
    def __eq__(self, other):
        if isinstance(other, EventCallable):
            return self._original_listener == other._original_listener
        if callable(other):
            return self._original_listener == other
        return False

    def __call__(self, *args, **kwargs):
        self._exec_count += 1
        if asyncio.iscoroutinefunction(self._listener):
            try:
                return asyncio.ensure_future(self._listener(*args, **kwargs), loop=self._loop)
            except:
                future = asyncio.Future(loop=self._loop)
                future.set_exception(sys.exc_info()[1])
                return future
        thr = threading.Thread(target=self._listener, args=args, kwargs=kwargs, daemon=True)
        thr.start()
        return thr

    @property
    def listener(self) -> Callable:
        return self._listener

    @property
    def original_listener(self) -> Callable:
        return self._original_listener

    @classmethod
    def once(cls, event_emitter: "EventEmitter", event_name: str, loop=None) -> Callable:
        def _once_decorator(func: Callable) -> Callable:
            self = cls(func, loop)
            def _once_wrapper(*args, **kwargs):
                try:
                    func(*args, **kwargs)
                finally:
                    event_emitter.remove_listener(event_name, func)
            async def _async_once_wrapper(*args, **kwargs):
                try:
                    await func(*args, **kwargs)
                finally:
                    event_emitter.remove_listener(event_name, func)
            self._listener = _async_once_wrapper if asyncio.iscoroutinefunction(func) else _once_wrapper
            return self
        return _once_decorator

class EventHandler:
    "Container for event listeners"

    def __init__(self):
        self._event_count = 0
        self._warned = False # type: bool
        self._handlers = [] # type: List[EventCallable]

    def append(self, listener: Callable) -> Callable:
        "Add a callable at the end of handlers chain"

        if not isinstance(listener, EventCallable):
            listener = EventCallable(listener)
        self._handlers.append(listener)
        return listener

    def prepend(self, listener: Callable) -> Callable:
        "Add a callable at the begining of handlers chain"

        if not isinstance(listener, EventCallable):
            listener = EventCallable(listener)
        self._handlers.insert(0, listener)
        return listener

    def remove(self, listener) -> bool:
        "Remove a callable from handlers chain"

        if not callable(listener):
            raise TypeError("listener is not callable")
        for event_callable in self._handlers:
            if event_callable._original_listener == listener:
                break
        else:
            return False
        self._handlers.remove(event_callable)
        return True

    def warn(self, event_emitter_class: Type["EventEmitter"], event_name: str):
        warnings.warn("Possible memory leak detected. {:d} {} listeners added to [{}]. Use max_listener to increase limit".format(len(self._handlers), event_name, event_emitter_class.__name__), ResourceWarning)
        self._warned = True

    @property
    def event_count(self) -> int:
        return self._event_count

    @property
    def warned(self) -> bool:
        return self._warned

    @property
    def handlers(self) -> List[EventCallable]:
        return self._handlers.copy()

    def __len__(self) -> int:
        return len(self._handlers)

    def __iadd__(self, listener: Callable):
        self.append(listener)
        return self

    def __isub__(self, listener: Callable):
        self.remove(listener)
        return self

    def __call__(self, *args, **kwargs) -> List[Union[asyncio.Future, threading.Thread]]:
        self._event_count += 1
        return [handler(*args, **kwargs) for handler in self._handlers]

    def __iter__(self):
        return iter(self._handlers)
            

class EventEmitter:
    "Event handling class"

    DEFAULT_MAX_LISTENER = 10

    def __init__(self):
        self.__handlers = {} # type: Dict[str, EventHandler]
        self.max_listener = self.DEFAULT_MAX_LISTENER

    def __create_if_not_exists(self, event_name: str):
        if event_name not in self.__handlers:
            self.__handlers[event_name] = EventHandler()

    def __count_check(self, event_name: str):
        if not self.__handlers[event_name].warned and len(self.__handlers[event_name]) > self.max_listener:
            self.__handlers[event_name].warn(self.__class__, event_name)

    def emit(self, *args, **kwargs):
        event_name = args[0]
        args = args[1:]
        handler = self.__handlers.get(event_name, EventHandler())
        handler(*args, **kwargs)

    def listener_count(self, event_name: str) -> int:
        if event_name not in self.__handlers:
            return 0
        return len(self.__handlers[event_name])
        
    def listeners(self, event_name: str) -> List[Callable]:
        return [event_callable.original_listener for event_callable in self.__handlers.get(event_name, EventHandler()).handlers]

    def on(self, event_name: str, listener: Callable):
        self.emit("newListener", event_name, listener)
        self.__create_if_not_exists(event_name)
        self.__handlers[event_name].append(listener)
        self.__count_check(event_name)
        return self

    def once(self, event_name: str, listener: Callable):
        self.emit("newListener", event_name, listener)
        listener = EventCallable.once(self, event_name)(listener)
        self.__create_if_not_exists(event_name)
        self.__handlers[event_name].append(listener)
        self.__count_check(event_name)
        return self

    add_listener = on

    def prepend_listener(self, event_name: str, listener: Callable):
        self.emit("newListener", event_name, listener)
        self.__create_if_not_exists(event_name)
        self.__handlers[event_name].prepend(listener)
        self.__count_check(event_name)
        return self

    def prepend_once_listener(self, event_name: str, listener: Callable):
        self.emit("newListener", event_name, listener)
        listener = EventCallable.once(self, event_name)(listener)
        self.__create_if_not_exists(event_name)
        self.__handlers[event_name].prepend(listener, once=True)
        self.__count_check(event_name)
        return self

    def remove_all_listeners(self, event_name: str):
        if event_name in self.__handlers:
            handlers = self.__handlers.pop(event_name)
            for event_callable in handlers: # type: EventCallable
                self.emit("removeListener", event_name, event_callable.original_listener)
        return self

    def remove_listener(self, event_name: str, listener: Callable):
        if event_name in self.__handlers:
            self.__handlers[event_name].remove(listener)
            if not len(self.__handlers[event_name]):
                del self.__handlers[event_name]
            self.emit("removeListener", event_name, listener)
        return self

    @property
    def max_listener(self) -> int:
        return self.__max_listener

    @max_listener.setter
    def max_listener(self, value: int):
        if not isinstance(value, int):
            value = int(value)
        self.__max_listener = value

    @property
    def event_names(self):
        return [event_name for event_name in self.__handlers.keys()]

    def raw_listeners(self, event_name: str) -> List[Callable]:
        return [event_callable.listener for event_callable in self.__handlers.get(event_name, EventHandler()).handlers]
