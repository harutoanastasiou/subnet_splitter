"""Public API for subnet_splitter.

Re-exports the two functions that callers should use.
"""
from subnet_splitter.core import split_into, split_for_hosts

__all__ = ["split_into", "split_for_hosts"]
