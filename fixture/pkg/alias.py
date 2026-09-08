"""Command alias resolution for a small CLI."""

ALIASES = {
    "co": "checkout",
    "st": "status",
    "br": "branch",
}


def resolve(cmd):
    # BUG: should fall back to the original command when there is no alias,
    # but currently returns None for unknown commands.
    return ALIASES.get(cmd)
