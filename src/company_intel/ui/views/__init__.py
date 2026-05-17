"""Dispatch table: each view name maps to a render() function."""
from . import company, disambig, disambiguating, input, researching

_VIEWS = {
    "input": input.render,
    "disambiguating": disambiguating.render,
    "disambig": disambig.render,
    "researching": researching.render,
    "company": company.render,
}


def render(view_name: str) -> None:
    """Render the view by name. Falls back to 'input' for unknown names."""
    _VIEWS.get(view_name, input.render)()
