"""
Local override for pytesseract, which has no built-in p4a recipe.

WHY THIS EXISTS:
python-for-android tries to auto-install "recipe-less" pure-Python
requirements (pytesseract, requests, etc.) in one batch using pip's
--only-binary resolver. Because pytesseract depends on Pillow, and
Pillow has no matching pre-built wheel for the Android target
platform (Pillow is built separately via its own p4a recipe with
native code), pip's resolver fails with a confusing "conflicting
dependencies" error across pytesseract's versions.

Giving pytesseract its own tiny recipe makes p4a install it directly
from its PyPI source (no pip dependency resolution against Pillow
needed) and simply declares a build-order dependency on the
already-compiled 'pillow' recipe instead.
"""

from pythonforandroid.recipe import PythonRecipe


class PytesseractRecipe(PythonRecipe):
    name = 'pytesseract'
    version = '0.3.13'
    url = 'https://files.pythonhosted.org/packages/source/p/pytesseract/pytesseract-{version}.tar.gz'
    depends = ['setuptools', 'pillow']
    call_hostpython_via_targetpython = False


recipe = PytesseractRecipe()
