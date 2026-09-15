"""
Local override for python-for-android's built-in "reportlab" recipe.

WHY THIS EXISTS:
The default p4a recipe downloads reportlab's source from
https://hg.reportlab.com/hg-public/reportlab/... . That server has
started rejecting automated/CI requests with HTTP 403 Forbidden,
which breaks GitHub Actions builds.

Since ReportLab 4.x publishes as a pure-Python package on PyPI (the
optional C accelerators are now separate packages - rl_accel,
rl_renderpm - which this app does not need for basic PDF generation),
we can safely install it as a plain Python package straight from
PyPI's reliable CDN instead. No compilation required, so this is
both simpler and less fragile than the original recipe.
"""

from pythonforandroid.recipe import PythonRecipe


class ReportlabRecipe(PythonRecipe):
    name = 'reportlab'
    version = '4.4.7'
    url = 'https://files.pythonhosted.org/packages/source/r/reportlab/reportlab-{version}.tar.gz'
    depends = ['setuptools']
    call_hostpython_via_targetpython = False


recipe = ReportlabRecipe()
