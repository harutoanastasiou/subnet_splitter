# subnet_splitter

Divide an IPv4 CIDR block into N equal-sized subnets, or a single subnet sized for a host count. Standard library only.

```python
from subnet_splitter import split_into, split_for_hosts

split_into("10.0.0.0/24", 4)
# ['10.0.0.0/26', '10.0.0.64/26', '10.0.0.128/26', '10.0.0.192/26']

split_for_hosts("10.0.0.0/24", 50)
# ['10.0.0.0/26']
```

## Why

`ipaddress.IPv4Network.subnets()` already divides a block, and working out the right prefix for a given host count is a couple of lines of arithmetic. This library exists so callers do not re-derive either step and so the edge cases (non-power-of-two counts, blocks too small to satisfy the request, the /31 and /32 usable-host convention) are handled in one place with a single error type.

## Decisions

- IPv4 only. If you need IPv6, this is the wrong library.
- `split_into(cidr, n)` requires `n` to be a power of two. Equal-sized splitting has no honest answer for other counts; rather than return unequal pieces, we refuse.
- `split_for_hosts(cidr, hosts)` returns a list containing exactly one subnet — the largest prefix whose usable-host count fits `hosts`, carved from the start of the parent. The list shape is deliberate so the two functions share a return type.
- Usable hosts means all addresses minus the network and broadcast addresses. Prefixes /31 and /32 therefore offer zero usable hosts under this rule.

## Edges you will hit

- Asking `split_into` for more subnets than the parent can hold raises `ValueError`. A /30, for instance, cannot be split into 8 pieces.
- Asking `split_for_hosts` for more usable hosts than the parent can ever provide raises `ValueError`.
- Both functions reject `bool` as a count argument, because `bool` is a subclass of `int` in Python and silently accepting `True` as `1` is a frequent source of bugs.
