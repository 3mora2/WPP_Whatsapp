import inspect
from asyncio import ProactorEventLoop
from types import FunctionType


def async_to_sync(func: FunctionType):
    def wrapper(self, *args, **kwargs):
        if not inspect.isfunction(func):
            raise Exception(f"{func} Not Function")
        if inspect.iscoroutinefunction(func):
            future = func(self, *args, **kwargs)
            if inspect.iscoroutine(future):
                self.loop: "ProactorEventLoop"
                # try:
                return self.loop.run_until_complete(func(self, *args, **kwargs))
                # except RuntimeError :
                #     return asyncio.ensure_future(future, loop=self.loop)

            return future

    return wrapper
