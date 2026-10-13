"""Declare the service surface separately from transport and dispatch logic."""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType
from typing import Mapping

from .contracts import Operation


def snake(name: str) -> str:
    """Convert public legacy names without splitting acronyms into letters."""
    name = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name.rstrip("_"))
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower()


@dataclass(frozen=True)
class ServiceDefinition:
    name: str
    layers: tuple[type, ...]
    extra_operations: tuple[Operation, ...] = ()

    def operations(self) -> Mapping[str, Operation]:
        declared = {}
        for layer in self.layers:
            for name, function in vars(layer).items():
                if not name.startswith("_") and inspect.iscoroutinefunction(function):
                    declared[snake(name)] = function
        for function in self.extra_operations:
            declared[snake(function.__name__)] = function
        return MappingProxyType(declared)


@lru_cache(maxsize=1)
def service_definitions() -> tuple[ServiceDefinition, ...]:
    # Lazy imports resolve the legacy facade's compatibility installation first.
    from WPP_Whatsapp.api.layers.BusinessLayer import BusinessLayer
    from WPP_Whatsapp.api.layers.CatalogLayer import CatalogLayer
    from WPP_Whatsapp.api.layers.CommunityLayer import CommunityLayer
    from WPP_Whatsapp.api.layers.ControlsLayer import ControlsLayer
    from WPP_Whatsapp.api.layers.GroupLayer import GroupLayer
    from WPP_Whatsapp.api.layers.LabelsLayer import LabelsLayer
    from WPP_Whatsapp.api.layers.ListsLayer import ListsLayer
    from WPP_Whatsapp.api.layers.NewsletterLayer import NewsletterLayer
    from WPP_Whatsapp.api.layers.ProfileLayer import ProfileLayer
    from WPP_Whatsapp.api.layers.RetrieverLayer import RetrieverLayer
    from WPP_Whatsapp.api.layers.SenderLayer import SenderLayer
    from WPP_Whatsapp.api.layers.StatusLayer import StatusLayer
    from WPP_Whatsapp.api.layers.UILayer import UILayer
    from WPP_Whatsapp.api.Whatsapp import Whatsapp

    # Session cleanup/injection methods must never become message operations.
    message_methods = (
        "downloadFile_",
        "downloadMedia_",
        "getMessages_",
        "getMessageById_",
        "takeScreenshot_",
        "useHere_",
        "logout_",
        "rejectCall_",
    )
    return (
        ServiceDefinition(
            "messages",
            (SenderLayer, RetrieverLayer),
            tuple(getattr(Whatsapp, name) for name in message_methods),
        ),
        ServiceDefinition("groups", (GroupLayer,)),
        ServiceDefinition("catalog", (CatalogLayer, BusinessLayer)),
        ServiceDefinition("communities", (CommunityLayer,)),
        ServiceDefinition("newsletters", (NewsletterLayer,)),
        ServiceDefinition("profile", (ProfileLayer,)),
        ServiceDefinition("lists", (ListsLayer,)),
        ServiceDefinition("labels", (LabelsLayer,)),
        ServiceDefinition("chats", (RetrieverLayer, ControlsLayer, UILayer)),
        ServiceDefinition("status", (StatusLayer,)),
    )
