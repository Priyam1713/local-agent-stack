from pkg.textutil import normalise


def render(titles):
    """Render titles as a bullet list, one normalised title per line."""
    return "\n".join(f"- {normalise(t)}" for t in titles)
