from hypothesis import given
from hypothesis.strategies import text
import re
import sys
sys.path.append('../')
import jupman_tools as jmt
from jupman_tools import ignore_spaces
from jupman_tools import Jupman
import pytest 
from sphinx.application import Sphinx
import os

def test_jupman_constructor():
    jm = Jupman()
    # only testing the vital attrs
    assert jm.filename == 'jupman'
    #NOTE: putting '/' at the end causes exclude_patterns to not work !
    assert jm.build == '_build' 
    assert jm.generated == '_static/generated'

class MockSphinx:
    def add_config_value(self, a,b,c):
        pass
    def add_transform(self, a):
        pass
    def add_javascript(self, a):
        pass
    def add_stylesheet(self, a):
        pass

def test_setup():
    if os.path.isdir('_build/test'):
        jmt.delete_tree('_build/test', '_build/test')
    if os.path.isdir('_build/test-generated'):
        jmt.delete_tree('_build/test-generated', '_build/test-generated')

    import conf
    
    mockapp = MockSphinx()
    conf.jm.build = '_build/test'
    conf.jm.generated = '_build/test-generated'
    
    conf.setup(mockapp)
    assert os.path.isfile(os.path.join(conf.jm.generated, 'jupyter-intro.zip'))
    assert os.path.isfile(os.path.join(conf.jm.generated, 'python-intro.zip'))
    assert os.path.isfile(os.path.join(conf.jm.generated, 'tools-intro.zip'))

def test_ignore_spaces():
    
    with pytest.raises(ValueError):
        ignore_spaces("")

    p = re.compile(ignore_spaces(" a    b"))
    assert p.match(" a b")
    assert p.match(" a  b")
    assert p.match(" a  b ")
    assert p.match(" a  b  ")
    assert p.match(" a  b\n")
    assert p.match("   a  b\n")
    assert not p.match(" ab")
    assert not p.match("c b")
    
    

    
    