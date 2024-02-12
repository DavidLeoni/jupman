
import sys
sys.path.append('../')
sys.path.append('.')  # good lord, without this debugging in VSCode doesn't work

#keep it first so we don't get deprecation warnings
import jupman_tools as jmt

from hypothesis import given
from hypothesis.strategies import text

from jupman_tools import ignore_spaces, tag_regex, JupmanConfig, JupmanContext
import pytest 
import re
from sphinx.application import Sphinx
import os
import nbformat

def clean():
    if os.path.isdir('_build/test'):
        jmt.delete_tree('_build/test', '_build/test')
        
    if os.path.isdir('_build/test-generated'):
        jmt.delete_tree('_build/test-generated', '_build/test-generated')

    if os.path.isdir('_build/test-tmp'):
        jmt.delete_tree('_build/test-tmp', '_build/test-tmp')

def prep_jm(jm : JupmanConfig):
    jm.build = '_build/test'
    jm.generated = '_build/test-generated'
    jm.manual = 'students'    

def make_jm() -> JupmanConfig:
    jm = JupmanConfig()
    prep_jm(jm)
    return jm


def make_sphinx_config() -> dict:
    sc = {}
    sc['author'] = 'People That Write a Lot'
    sc['jm'] = make_jm()
    #sc['include_patterns'] = ['**']
    #sc['exclude_patterns'] = []
    return sc


def make_jupman_context() -> JupmanContext:
    sc = make_sphinx_config()
    return JupmanContext(sc, '_private/test', False, '')
  
def make_jcxt_gitignore_non_existing():
    """
        @since 3.6
    """
    jcxt = make_jupman_context()

    jmt.init_exclude_patterns(jcxt.jm, jcxt.exclude_patterns, gitignore_path='flying-pig.gitignore')
    return jcxt

def make_jcxt_gitignored():
    """
        @since 3.6
    """
    jcxt = make_jupman_context()
    jmt.init_exclude_patterns(jcxt.jm, jcxt.exclude_patterns)
    return jcxt

def make_jcxt_zip_ignored():
    """
        @since 3.6
    """
    jcxt = make_jcxt_gitignored()
    jcxt.jm.zip_ignored.extend(['**/big-*'])
    return jcxt
  
  
@pytest.fixture
def tconf():
    clean()

    import conf

    prep_jm(conf.jm)
    
    conf.test_tmp = os.path.join('_build', 'test-tmp')
    os.makedirs(conf.test_tmp )
    
    return conf

def make_nb_resources(path):
        
    path = path.rstrip('.ipynb')
        
    dirname = os.path.dirname(path)
    basename = os.path.basename(path)
    
    return {   
        'metadata': {
                        'path': dirname, # '/home/da/Da/prj/jupman/prj/jupyter-example'
                    },
        'nbsphinx_docname': path,
        'nbsphinx_save_notebook': '_build/test/.doctrees/nbsphinx/' + basename +  '.ipynb',
        'output_files_dir': '../_build/test/html/.doctrees/nbsphinx',
        'unique_key': path.replace('/', '_')
    }
