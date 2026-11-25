from pkg.textutil import normalize


def render(titles):
    return "\n".join(f"- {normalize(t)}" for t in titles)
