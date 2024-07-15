from __future__ import annotations

from typing import TypeVar

from django import template

__all__ = [
    "divide",
    "replace",
    "split_even_and_odd",
]


register = template.Library()
T = TypeVar("T")


@register.filter
def replace(value: str, arg: str) -> str:
    to_replace, replace_with = arg.split("|", maxsplit=1)
    return value.replace(to_replace, replace_with)


@register.filter
def split_even_and_odd(value: list[T]) -> list[tuple[int, T]]:
    return [(i % 2 == 0, val) for i, val in enumerate(value)]


@register.filter
def divide(value: int, arg: int) -> int:
    return int(value) // int(arg)
