"""Pure standard-library IPv4 CIDR splitting.

Interpretation decisions (stated in the README, enforced here):
  * IPv4 only.
  * "N equal-sized subnets" requires the parent CIDR's prefix to be
    extendable by exactly ceil(log2(N)) bits. If N is not a power of two
    and the rounded-up count exceeds the remaining host bits, we refuse
    rather than silently returning unequal pieces.
  * "Subnets sized for a host count" returns the largest prefix whose
    usable host count fits the requested number, carved from the START of
    the parent in a single contiguous block (not a list of many). If the
    parent cannot hold that block, we refuse.
  * "Usable hosts" counts all addresses except the network address and
    the broadcast address, per RFC 1122 host bits all-zero / all-one
    conventions. Prefixes /31 and /32 yield 0 usable hosts by this rule.
  * Output is a list of strings in "a.b.c.d/nn" form, sorted by network
    address ascending. We sort defensively because some callers rely on
    order and IPv4 math being in network-byte order is non-obvious.
"""

import ipaddress
import math

__all__ = ["split_into", "split_for_hosts"]


def split_into(cidr: str, n: int) -> list[str]:
    """Split an IPv4 CIDR block into ``n`` equal-sized subnets.

    Raises ``ValueError`` if ``n`` is not a positive integer, if the CIDR
    is not a valid IPv4 network, or if the parent cannot be divided into
    exactly ``n`` equal pieces (which happens when ``log2(n)`` is not an
    integer, or when the resulting prefix would exceed /32).
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise ValueError("n must be an int")
    if n <= 0:
        raise ValueError("n must be a positive integer")

    # math.log2 returns float; int() is safe here because we check the
    # power-of-two property before trusting bits.
    bits = int(math.log2(n))
    if (1 << bits) != n:
        raise ValueError("n must be a power of two")

    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid IPv4 CIDR: {cidr!r}") from exc

    if network.version != 4:
        raise ValueError("only IPv4 is supported")

    new_prefix = network.prefixlen + bits
    if new_prefix > 32:
        raise ValueError(
            f"splitting into {n} requires prefix /{new_prefix}, exceeds /32"
        )

    # list(network.subnets(...)) is deterministic and ascending by network
    # address; we still sort defensively so the contract is explicit.
    subnets = sorted(network.subnets(new_prefix=new_prefix),
                     key=lambda s: int(s.network_address))
    return [str(s) for s in subnets]


def split_for_hosts(cidr: str, hosts: int) -> list[str]:
    """Return a single subnet carved from ``cidr`` that fits ``hosts``.

    The result contains exactly one element (a list is returned for a
    consistent shape across this library). The carved subnet is the
    largest prefix whose usable-host count is at least ``hosts``, placed
    at the start of the parent block.

    Raises ``ValueError`` if ``hosts`` is not a positive integer, the CIDR
    is invalid or not IPv4, or no prefix in the parent can satisfy the
    request.
    """
    if not isinstance(hosts, int) or isinstance(hosts, bool):
        raise ValueError("hosts must be an int")
    if hosts <= 0:
        raise ValueError("hosts must be a positive integer")

    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid IPv4 CIDR: {cidr!r}") from exc

    if network.version != 4:
        raise ValueError("only IPv4 is supported")

    # Find the smallest new_prefix (largest block) whose usable hosts fit.
    # We scan from /32 downward to the parent prefix; the first prefix that
    # can host ``hosts`` wins (smallest block that fits, which is the
    # largest acceptable prefix). Usable hosts is monotonic decreasing in
    # prefix length, so the earliest match from /32 down is the tightest
    # fit carved from the start of the parent.
    for new_prefix in range(32, network.prefixlen - 1, -1):
        block = ipaddress.IPv4Network((int(network.network_address), new_prefix))
        if not block.subnet_of(network):
            continue
        usable = block.num_addresses - 2 if new_prefix <= 30 else 0
        if usable >= hosts:
            return [str(block)]

    raise ValueError(
        f"no subnet of {cidr} can host {hosts} usable addresses"
    )
