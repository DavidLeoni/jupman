import sys
sys.path.append('../')
sys.path.append('.')  # good lord, without this debugging in VSCode doesn't work

#keep it first so we don't get deprecation warnings
import jupman_tools as jmt

from hypothesis import given
from pprint import pprint
from hypothesis.strategies import text
from jupman_tools import ignore_spaces, tag_regex, JupmanConfig, SphinxConfig, JupmanContext, JupmanError, JupmanNotFoundError, FileKinds, JupmanPreprocessorError, JupmanEmptyChapterError, JupmanUnsupportedError
import pytest 
import re
from sphinx.application import Sphinx
import os
import nbformat
import time
import filecmp
import shutil
import nbsphinx
import inspect
from jupman_tools import debug    
from pprint import pformat

from common_test import clean, make_jupman_context, make_sphinx_config, make_jcxt_gitignore_non_existing, make_jcxt_gitignored, make_jcxt_zip_ignored, make_jm, make_nb_resources,  tconf
import datetime

class MockSphinx:
    def add_config_value(self, a,b,c):
        pass
    def add_transform(self, a):
        pass
    def add_javascript(self, a):
        pass
    def add_stylesheet(self, a):
        pass

def test_setup(tconf):
    """ This test runs an entire build of jupman itself
    """
        
    mockapp = MockSphinx()
        
    tconf.setup(mockapp)
    
    # so tests run smoothly also on non-jupman projects
    if os.path.exists('jupyter-example'):
        assert os.path.isfile(os.path.join(tconf.jm.generated, 'jupyter-example.zip'))        
    if os.path.exists('python-example'):
        assert os.path.isfile(os.path.join(tconf.jm.generated, 'python-example.zip'))
    if os.path.exists('jup-and-py-example'):
        assert os.path.isfile(os.path.join(tconf.jm.generated, 'jup-and-py-example.zip'))
    if os.path.exists('challenge-example'):
        assert os.path.isfile(os.path.join(tconf.jm.generated, 'challenge-example.zip'))

    # test reproducible build zips  https://github.com/DavidLeoni/jupman/issues/60
        
    if os.path.exists('jup-and-py-example'):
            
        zpath1 = os.path.join(tconf.jm.generated, 'jup-and-py-example.zip')     
        
                        
        zpath2 = os.path.join(tconf.test_tmp, 'jup-and-py-example.zip')
        
        
        shutil.copyfile(zpath1, zpath2)        
        time.sleep(2)
        tconf.setup(mockapp)
                    
        assert filecmp.cmp(zpath1, zpath2, shallow=False)


jcxtfs = [ make_jcxt_gitignore_non_existing, 
           #make_jcxt_gitignored
           ]
@pytest.mark.parametrize("jcxtf", jcxtfs)
def test_is_zip_ignored_after_exclude_init(jcxtf):
    """ WARNING: since some files we use here are gitignored, you may not have them on your system
                 (or when a build is performed on github). Test should 'pass' anyway because
                 when is_zip_ignored doesn't find an existing file, should return True anyway
                 
                 Maybe in the future we may recreate them automatically somehow
        @since 3.6
    """
    debug(f"Creating {jcxtf.__name__}")
    jcxt = jcxtf()
    
    cchal = "_test/chap1-complete/c-chal-sol.ipynb"
    dchal = "_test/chap1-complete/d_chal_sol.py"
        
    assert jmt.is_zip_ignored(jcxt, jcxt.jm.build)
    assert jmt.is_zip_ignored(jcxt, jcxt.jm.generated) 
    assert jmt.is_zip_ignored(jcxt, '_private')
    assert jmt.is_zip_ignored(jcxt, cchal)
    assert jmt.is_zip_ignored(jcxt, dchal)
    
    assert jmt.is_zip_ignored(jcxt, '.git/index')
    assert jmt.is_zip_ignored(jcxt, '.git/')        
    assert jmt.is_zip_ignored(jcxt, '.git/info/exclude')    
    assert jmt.is_zip_ignored(jcxt, '.gitignore')
    assert jmt.is_zip_ignored(jcxt, '.gitattributes')
    
    # additional check in case you don't have the files on your system:
    
    assert jcxt.jm.build in jcxt.exclude_patterns
    assert jcxt.jm.generated in jcxt.exclude_patterns 
    assert '_private' in jcxt.exclude_patterns
    assert "**-chal-sol.*" in jcxt.exclude_patterns
    assert "**-chal-sol.*" in jcxt.exclude_patterns
    
    assert '.git' in jcxt.exclude_patterns
    assert '.gitignore' in jcxt.exclude_patterns
    assert '.gitattributes' in jcxt.exclude_patterns
