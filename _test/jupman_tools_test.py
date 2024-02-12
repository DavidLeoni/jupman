import sys
sys.path.append('../')
sys.path.append('.')  # good lord, without this debugging in VSCode doesn't work

#keep it first so we don't get depreation warnings
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



def test_detect_release():
    res =  jmt.detect_release()
    assert res == 'dev' or len(res.split('.')) >= 2

def test_get_version():
    res =  jmt.get_version(jmt.detect_release())
    assert res == 'dev' or len(res.split('.')) == 2


def test_parse_date():
    assert jmt.parse_date('2000-12-31') == datetime.datetime(2000,12,31)

    with pytest.raises(Exception):
        jmt.parse_date('2000-31-12')

def test_parse_date_str():
    assert jmt.parse_date_str('2000-12-31') == '2000-12-31'
    
    with pytest.raises(Exception):
        jmt.parse_date_str('2000-31-12')


def test_date_to_human():
    assert jmt.date_to_human('2000-12-31', 'en') == 'Sun 31, Dec 2000'
    assert jmt.date_to_human('2000-12-31', 'it') == 'Dom 31, Dic 2000'
    assert jmt.date_to_human(jmt.parse_date('2000-12-31'), 'en') == 'Sun 31, Dec 2000'
    assert jmt.date_to_human(jmt.parse_date('2000-12-31'), 'it') == 'Dom 31, Dic 2000'


def test_jupman_constructor():
    jm = JupmanConfig()
    # only testing the vital attrs
    assert jm.filename == 'jupman'
    #NOTE: putting '/' at the end causes exclude_patterns to not work !
    assert jm.build == '_build' 
    assert jm.generated == '_static/generated'


def test_uproot():
    assert jmt.uproot('jupman.py') == ''
    assert jmt.uproot('_test/') == '../'
    assert jmt.uproot('_static/img/cc-by.png') == '../../'    
    assert jmt.uproot('_test/test-chapter/population.csv') == '../../'
    # this is supposed to be a directory
    
    assert jmt.uproot('_static/img') == '../../'
    
    # TODO review behaviour an non-existing paths
    assert jmt.uproot('_test/non-existing') == '../../'    
    #assert jmt.uproot('_static/img/non-existing1') == '../../../'
    #assert jmt.uproot('_static/img/non-existing1/') == '../../../'
    #assert jmt.uproot('_static/img/non-existing1/non-existing2') == '../../../'
    #assert jmt.uproot('_static/img/non-existing1/non-existing2/') == '../../../'
    
    

def test_replace_pyrel():

    assert jmt.replace_py_rel("""import sys
sys.do_something()""", 'python-example').strip() ==  """import sys
sys.do_something()"""


    assert jmt.replace_py_rel("""
import sys
sys.path.append('../')
import jupman

    """, 'python-example').strip() ==  'import jupman'


    assert jmt.replace_py_rel("""
import sys
sys.path.append('../')
import jupman
sys.do_something()
    """, 'python-example').strip() ==  """import sys
import jupman
sys.do_something()"""



def test_is_zip_ignored_non_existing_file():
    """ Since 3.6 non existing files are considered as zip_ignored
    
        @since 3.6
    """
    jcxt = make_jupman_context()
    assert jmt.is_zip_ignored(jcxt, 'flying.pig')
    

def test_is_zip_ignored_default():
    """ @since 3.6
    """
            
    jcxt = make_jupman_context()
 
    assert os.path.isfile('index.ipynb')
    assert not jmt.is_zip_ignored(jcxt, 'index.ipynb')
    
    assert os.path.isfile('manual/editing.ipynb')
    assert not jmt.is_zip_ignored(jcxt, 'manual/editing.ipynb')



    
    
def test_is_zip_ignored_big_files():
    """
        @since 3.6
    """
    
    jcxt = make_jcxt_zip_ignored()
    assert jmt.is_zip_ignored(jcxt, '_test/zip1-complete/big-dataset.csv')
    assert jmt.is_zip_ignored(jcxt, '_test/zip1-complete/big-output.csv')
    assert jmt.is_zip_ignored(jcxt, '_test/zip1-complete/big-expected-output.csv')
    assert jmt.is_zip_ignored(jcxt, '_test/zip1-complete/vid/big-video.mp4')
    
    assert not jmt.is_zip_ignored(jcxt, '_test/zip1-complete/small-dataset.csv')


def test_is_zip_ignored_relative_paths():
    """
        @since 3.6
    """

    p = '_test/filtering/'
    assert os.path.isfile(p + 'c.t')
    assert os.path.isfile(p + 's/c.t')
        
    jcxt = make_jcxt_zip_ignored()
    jcxt.jm.zip_ignored.append('**/c.t')

    assert jmt.is_zip_ignored(jcxt, p + 'c.t')
    assert jmt.is_zip_ignored(jcxt, p + 's/c.t')
    assert not jmt.is_zip_ignored(jcxt, p + 'd.t')
    
    
def test_is_zip_ignored_absolute_paths():
    """
        @since 3.6
    """
    p = '_test/filtering/'
    assert os.path.isfile(p + 'c.t')
    assert os.path.isfile(p + 's/c.t')
    
    
    jcxt = make_jcxt_zip_ignored()
    jcxt.jm.zip_ignored.append(p + 'c.t')
    
    assert jmt.is_zip_ignored(jcxt, p + 'c.t')
    assert not jmt.is_zip_ignored(jcxt, p + 's/c.t')
    
def test_sphinx_get_matching_files():
    """ @since 3.6
    """
    import sphinx
    jcxt = make_jcxt_gitignored()
    
    filtered_existing_paths = list(sphinx.util.matching.get_matching_files('',
                                   ['**'],
                                   jcxt.exclude_patterns + sphinx.project.EXCLUDE_PATHS))
    for p in filtered_existing_paths:
        assert not p.startswith('_private')

def test_sphinx_filter_root_files():
    """ @since 3.6
    """
    assert jmt._sphinx_filter([], {}, ['**'], []) == []
    assert jmt._sphinx_filter(['README.md'], {}, ['**'], []) == ['README.md']
    assert jmt._sphinx_filter(['README.md'], {}, ['README.md'], []) == ['README.md']
    assert jmt._sphinx_filter(['README.md'], {}, ['**'], ['README.md']) == []   

def test_sphinx_filter_sub_folders():
    """ @since 3.6
    """
    #note: exclude/include work by looking at actual files
    
    j = '_test/zip1-complete/j-sol.ipynb'
    n = '_test/test-chapter/nb-sol.ipynb'
    
    assert os.path.isfile(j)
    assert os.path.isfile(n)
    
    assert jmt._sphinx_filter(  [j, n],
                                {},
                                ['**'], 
                                ['_test/test-chapter'], 
                             ) == [j]  

    
    assert jmt._sphinx_filter( [j, n],
                               {},
                               ['_test/test-chapter/**'], 
                               []) == [n]    
    

def test_sphinx_filter_2ast_slash():
    """ Differently from git, Sphinx DOES *NOT* match **/folder with a folder in root
        
        @since 3.6
    """    
    
    nb = '_test/test-chapter/nb-sol.ipynb'
    
    assert jmt._sphinx_filter(  [nb],
                                {},
                                ['**'], 
                                ['**/_test/test-chapter'], 
                             ) == [nb]    
    assert jmt._sphinx_filter(  [nb],
                                {},
                                ['**'], 
                                ['/**/_test/test-chapter'], 
                             ) == [nb]
 
temp_path = None
temp_file_number = 0
def sf(text,paths,incl,excl):
    """ 
    Creates a 123.gitignore temporary file filled with provided text 
    and return the sphinx filtered files
    @since 3.6
    """
    global temp_file_number
    
    jcxt = make_jupman_context()
    p = temp_path / f"t{temp_file_number}.gitignore"
    p.write_text(text)
    temp_file_number += 1
    jmt.init_exclude_patterns(jcxt.jm, excl, p)
    return jmt._sphinx_filter(paths,{},incl,excl) 

 
def test_sphinx_filter_edge_cases(tmp_path):
    """
        @since 3.6
    """
    global temp_path # silly pytest workaround
    temp_path = tmp_path
    
    b = "_test/filtering"
    bi = f"{b}/**"
    x = f"{b}/x"
    y = f"{b}/y"
    ct = f"{b}/c.t"
    dt = f"{b}/d.t"
    et = f"{b}/s/e.t"
    ft = f"{b}/s/f.t"
    ALL = [f"{b}/**"]
    
    
    assert sf(f"", [f"{b}/x"],[f"{b}/x"],[f"{b}/x"]) == []  # sphinx excl has prio over incl
    assert sf(f"", [f"{b}/x"],ALL,[f"{b}/x"]) == []  # excl has prio over incl
    assert sf(f"", [],[f"{b}/x"],[]) == []  
    assert sf(f"", [f"{b}/x"],[f"{b}/x"],[]) == [f"{b}/x"]
    assert sf(f"", [f"{b}/c.t"],ALL,[f"*.t"]) == [f"{b}/c.t"]  # *.t in sphinx looks only in root
    assert sf(f"", [f"{b}/c.t"],ALL,[f"**.t"]) == []  
    assert sf(f"", [f"{b}/c.t"],ALL,[f"**/*.t"]) == []
    assert sf(f"", [f"{b}/x"],ALL,[]) == [f"{b}/x"]
    
    
def test_sphinx_filter_exclude_patterns_negated(tmp_path):
    """ igittigitt 2.1.2 doesn't support negated patterns,
        so in jupman 3.6 we just drop support for them.
        
        @since 3.6
    """
    global temp_path # silly pytest workaround
    temp_path = tmp_path
    b = "_test/filtering"
    
    gt  = f"""
    *.t
    !{b}/c.t
    """
    with pytest.raises(JupmanUnsupportedError):
        sf(gt, [f"{b}/c.t"], ['**'], []) 
        
    #assert sf(gt, [f"{b}/c.t"], ['**'], []) == [f"{b}/c.t"] 

def test_sphinx_filter_non_empty_folder(tmp_path):
    """ Non-empty folders should be detected in filters 
        @since 3.6
    """
    global temp_path # silly pytest workaround
    temp_path = tmp_path
    b = "_test/filtering"
    
    assert f"{b}/s" in sf(f"", [f"{b}/s"], ['**'], [])  
    
    
    
def test_sphinx_filter_empty_folder(tmp_path):
    """ Currently empty folders are not detected in filters 
        which is actually NOT desirable but we can live with it
        @since 3.6
    """
    global temp_path # silly pytest workaround
    temp_path = tmp_path
    b = "_test/filtering"
    ALL = [f"{b}/**"]
    
    assert f"{b}/empty" not in sf(f"", [f"{b}/empty"], ['**'], [])  
    
def test_sphinx_filter_file_dot_asterisk(tmp_path):
    """@since 3.6
    """
    global temp_path # silly pytest workaround
    temp_path = tmp_path
    b = "_test/filtering"
    ALL = [f"{b}/**"]
    
    assert sf(f"{b}/x",     [f"{b}/x"],ALL,[])   == []     
    assert sf(f"{b}/c.t",   [f"{b}/c.t"],ALL,[]) == [] 
    assert sf(f"{b}/x.*",   [f"{b}/x"],ALL,[])   == [f"{b}/x"]  
    assert sf(f"{b}/c.t.*", [f"{b}/c.t"],ALL,[]) == [f"{b}/c.t"]  

def test_sphinx_filter_file_2ast_ast_dot(tmp_path):    
    """@since 3.6
    """
    global temp_path # silly pytest workaround
    temp_path = tmp_path
    b = "_test/filtering"
    ALL = [f"{b}/**"]
    
    assert f"{b}/c.t" not in sf("**/*.t", [f"{b}/c.t"],ALL,[])
    
    
def test_sphinx_filter_dir_slash(tmp_path):    
    """@since 3.6
    """
    global temp_path # silly pytest workaround
    temp_path = tmp_path
    b = "_test/filtering"
    ALL = [f"{b}/**"]
    
    
    # NOTE: these two weren't working as igittgitt 2.1.2 only provides **/_test **/_test/**/* 
    #       as a workaround I tweked igittgitt call to also a '_test' with '**/' discarded
    assert sf("_test",              ["_test/filtering/c.t"],ALL,[]) == []
    assert sf("_test/",             ["_test/filtering/c.t"],ALL,[]) == []
    
    assert sf("_test/*",            ["_test/filtering/c.t"],ALL,[]) == []  
    assert sf("_test/**",           ["_test/filtering/c.t"],ALL,[]) == [] 
    assert sf("/_test",             ["_test/filtering/c.t"],ALL,[]) == []
    assert sf("_test/filtering",    ["_test/filtering/c.t"],ALL,[]) == []
    assert sf("_test/filtering/",   ["_test/filtering/c.t"],ALL,[]) == []
    assert sf("_test/filtering/s",  ["_test/filtering/c.t"],ALL,[]) == ["_test/filtering/c.t"]
    assert sf("_test/filtering/s/", ["_test/filtering/c.t"],ALL,[]) == ["_test/filtering/c.t"]
    
    
def test_sphinx_filter_init_from_jupman_gitignore():
    """ Defaults present in .gitignore that gets expanded when imported
        @since 3.6
    """

    jcxt = make_jcxt_gitignored()
    
    assert '_build' in jcxt.exclude_patterns
    assert '**/build' in jcxt.exclude_patterns # test only this expansion as I'm lazy
    assert '__pycache__' in jcxt.exclude_patterns 
    assert '.ipynb_checkpoints' in jcxt.exclude_patterns
    assert '*.pyc' in jcxt.exclude_patterns
    assert '.cache' in jcxt.exclude_patterns
    assert '.pytest_cache' in jcxt.exclude_patterns
    assert '.vscode' in jcxt.exclude_patterns


    
def test_is_code_sol_to_strip():
    
    jcxt = make_jupman_context()
    jcxt.jpre_website = True
    solution = '# SOLUTION\nx=5\n'
    write_here = '# write here\nx=5\n'
    jupman_raise = '#jupman-raise\nx=5\n#/jupman-raise\n'
    jupman_strip = '#jupman-strip\nx=5\n#/jupman-strip\n'
        
    jupman_preprocess = '#jupman-preprocess\nbla\n'
    
    jupman_purge = '#jupman-purge\nx=5\n#/jupman-purge\n'
    jupman_purge_input = 'bla\n#jupman-purge-input\nbla\n'
    jupman_purge_output = 'bla\n#jupman-purge-output\nbla\n'
    jupman_purge_io = 'bla\n#jupman-purge-io\nbla\n'

    assert jmt.is_to_strip(jcxt, solution) == True
    assert jmt.is_to_strip(jcxt, write_here) == True
    assert jmt.is_to_strip(jcxt, jupman_raise) == True
    assert jmt.is_to_strip(jcxt, jupman_strip) == True
    assert jmt.is_to_strip(jcxt, jupman_purge) == True
    assert jmt.is_to_strip(jcxt, jupman_preprocess) == True    
    assert jmt.is_to_strip(jcxt, jupman_purge_input) == True
    assert jmt.is_to_strip(jcxt, jupman_purge_output) == True
    assert jmt.is_to_strip(jcxt, jupman_purge_io) == True

    assert jmt.is_code_sol(jcxt, solution) == True
    assert jmt.is_code_sol(jcxt, write_here) == True    
    assert jmt.is_code_sol(jcxt, jupman_raise) == True
    assert jmt.is_code_sol(jcxt, jupman_strip) == True
    assert jmt.is_code_sol(jcxt, jupman_purge) == False
    assert jmt.is_code_sol(jcxt, jupman_purge_io) == False
    assert jmt.is_code_sol(jcxt, jupman_purge_input) == False
    assert jmt.is_code_sol(jcxt, jupman_purge_output) == False
    assert jmt.is_code_sol(jcxt, jupman_preprocess) == False
    
    cx = """x = 9
#jupman-purge
# present neither in solution nor in exercises
# NOTE: this is NOT considered a solution
y = 'purged!'
#/jupman-purge
# after"""
    assert jmt.is_to_strip(jcxt, cx) == True
    assert jmt.is_code_sol(jcxt, cx) == False


def test_purge_tags():
    jcxt = make_jupman_context()
    jcxt.jpre_website = True

    # single tag directive
    
    assert jmt._purge_tags(jcxt, """
    bla
    #jupman-preprocess
    ble
    """) == '\n    bla\n    \n    ble\n    '
    
    # single tag directive
    
    assert jmt._purge_tags(jcxt, """#jupman-preprocess
    ble
    """) == '\n    ble\n    '
    
    
    # span tag purge directive, removes between
    assert jmt._purge_tags(jcxt, """
    bla
    #jupman-purge
    ble
    #/jupman-purge
    blo
    """) == '\n    bla\n    \n    blo\n    '
    
    # purge io directive, removes all
    assert jmt._purge_tags(jcxt, """
    bla
    #jupman-purge-io
    ble        
    """) == ''
    

    # purge input directive, removes all
    assert jmt._purge_tags(jcxt, """
    bla
    #jupman-purge-input
    ble        
    """) == ''

    # purge output directive, no effect
    assert jmt._purge_tags(jcxt, """
    bla
    #jupman-purge-output
    ble
    """) == '\n    bla\n    \n    ble\n    '

    
    # solution span tag
    
    assert jmt._purge_tags(jcxt, """
    #jupman-raise
    bla
    #/jupman-raise""") == '\n    \n    bla\n    '
    
    # solution span tag
    
    assert jmt._purge_tags(jcxt, """
    #jupman-strip
    bla
    #/jupman-strip""") == '\n    \n    bla\n    '
    
    assert jmt._purge_tags(jcxt, """
    bla
    #jupman-strip
    ble
    #/jupman-strip
    blo""") == '\n    bla\n    \n    ble\n    \n    blo'
    

def test_make_stripped_cell_id():
    assert jmt.make_stripped_cell_id('abc') == 'abc-stripped'
    assert jmt.make_stripped_cell_id('a'*64) == 'a'*(64-len('-stripped')) + '-stripped'
    assert jmt.make_stripped_cell_id('a'*60) == 'a'*(60-len('-stripped')) + '-stripped'




@pytest.mark.parametrize("replacer_fun", [jmt.replace_html_rel, jmt.replace_md_rel])
def test_replace_rel(replacer_fun):
    """ @since 3.5.4
    """
    
    fp = '_test/jupman_tools_test.py'    
    
    
    # note inside it calls uproot, needs this to be run from project root
    assert replacer_fun('<a href="../_static/img/hello.png">', fp) \
           == '<a href="_static/img/hello.png">'
    assert replacer_fun('<a target="_blank" href="../_static/img/hello.png">', fp) \
           == '<a target="_blank" href="_static/img/hello.png">'       
    assert replacer_fun('<img src="../_static/img/hello.png">', fp) \
           == '<img src="_static/img/hello.png">'
    assert replacer_fun('<img alt="bla" src="../_static/img/hello.png">', fp) \
           == '<img alt="bla" src="_static/img/hello.png">'
       
    assert replacer_fun('A B <img alt="cc-by-1243" src="../_static/img/cc-by.png"> C D', fp) \
           == 'A B <img alt="cc-by-1243" src="_static/img/cc-by.png"> C D'

    assert replacer_fun("""A <script   src="c.js" > </script>  B""", fp) == """A <script   src="c.js" > </script>  B"""    
    assert replacer_fun("""A <script   src="../c.js" ></script>  B""", fp) == """A <script   src="c.js" ></script>  B"""
    assert replacer_fun("""A <script   src="../c.js" defer="defer"></script>  B""", fp) \
            == """A <script   src="c.js" defer="defer"></script>  B"""
    assert replacer_fun("""A <script   src="../d/c.js" ></script>  B""", fp) == """A <script   src="d/c.js" ></script>  B"""
    
    assert replacer_fun("""A <style> @import "c.css"</style>  B""", fp) == """A <style> @import "c.css"</style>  B"""
    assert replacer_fun("""A <style> @import "../c.css"</style>  B""", fp) == """A <style> @import "c.css"</style>  B"""
    #multiple style imports are not supported, placed test to signal when we support them
    assert replacer_fun("""A <style>\n  @import "../c.css";@import "../d.css"\n</style>  B""", fp)  \
           != """A <style>\n  @import "c.css";@import "d.css"\n</style>  B"""

    assert replacer_fun('A\n<style>\n@import ../_static/css/ab.css;\n</style>\nB', fp) \
           == 'A\n<style>\n@import _static/css/ab.css;\n</style>\nB'            
    


    
    


                

def TODO_test_reproducible_build_html():
    
    """ NOTE: 2020 12: if img alt is not specified, a random id is assigned which makes build non-deterministic
    """    
    hpath1 = os.path.join(tconf.jm.build, 'html/jupman-tests.html')
    hpath2 = os.path.join(tconf.test_tmp, 'html/jupman-tests.html')
    shutil.copyfile(hpath1, hpath2)
    time.sleep(2)
    assert filecmp.cmp(zpath1, zpath2, shallow=False)

def test_tag_regex():
    
    with pytest.raises(ValueError):
        tag_regex("")

    p = re.compile(tag_regex(" a    b"))
    assert p.match(" a b")
    assert p.match(" a  b")
    assert p.match(" a  b ")
    assert p.match(" a  b  ")
    assert p.match(" a  b\n")
    assert p.match("   a  b\n")
    assert not p.match(" ab")
    assert not p.match("c b")

def test_write_solution_here():
    jm = make_jm()
    p = re.compile(jm.write_solution_here)    
    assert p.match(" # write here a b\nc")
    assert p.match(" # write here a   b c \nc\n1d")    
    assert p.match('#  write  here\n')
    #assert p.match('# write here')  # corner case, there is no \n    
    #assert p.match('# write here   ')  # corner case, there is no \n    

def test_span_pattern():
    jm = make_jm()
            
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#ab #/ab') == 'z'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#ab c #/ab') == 'z'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#ab\n#/ab') == 'z'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#ab\n#/ab') == 'z'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#ab #/ab c') == 'z c'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#ab #/ab\nc') == 'z\nc'
    assert re.sub(   jmt.span_pattern('ab'), 'z', ' #ab #/ab') == ' z'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#a b #/ab') == '#a b #/ab'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#ab #ab') == '#ab #ab'        
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#abc #/ab') == '#abc #/ab'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#abc#/abc') == '#abc#/abc'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#ab c #/ab w #ab d #/ab') == 'z w z'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#ab c #/ab\n#ab d #/ab') == 'z\nz'
    assert re.sub(   jmt.span_pattern('ab'), 'z', '#ab c #/ab #ab d #/ab') == 'z z'
    
    
    

def test_validate_code_tags():
    jcxt = make_jupman_context()
    assert jmt.validate_code_tags(jcxt, '# SOLUTION\nbla', 'some_file') == 1
    assert jmt.validate_code_tags(jcxt, '  # SOLUTION\nbla', 'some_file') == 1
    assert jmt.validate_code_tags(jcxt, 'something before  # SOLUTION\nbla', 'some_file') == 0
    assert jmt.validate_code_tags(jcxt, '#jupman-strip\nblabla#/jupman-strip', 'some_file') == 1
    assert jmt.validate_code_tags(jcxt, '#jupman-strip\nA#/jupman-strip #jupman-raise\nB#/jupman-raise', 'some_file') == 2
    
    assert jmt.validate_code_tags(jcxt, '#jupman-preprocess', 'some_file') == 0
    assert jmt.validate_code_tags(jcxt, '#jupman-purge\nblabla#/jupman-purge', 'some_file') == 0
    assert jmt.validate_code_tags(jcxt, '#jupman-purge-input\nA', 'some_file') == 0
    assert jmt.validate_code_tags(jcxt, '#jupman-purge-output\nA', 'some_file') == 0
    assert jmt.validate_code_tags(jcxt, '#jupman-purge-io\nA', 'some_file') == 0
    
    # pairs count as one
    assert jmt.validate_code_tags(jcxt, '#jupman-raise\nA#/jupman-raise', 'some_file') == 1
    assert jmt.validate_code_tags(jcxt, """
    hello
    #jupman-raise
    something
    #/jupman-raise
    #jupman-raise
    bla
    #/jupman-raise""", 'some_file') == 2

def test_validate_markdown_tags():
    jcxt = make_jupman_context()

    assert jmt.validate_markdown_tags(jcxt, '**ANSWER**: hello', 'some_file') == 1
    assert jmt.validate_markdown_tags(jcxt, '  **ANSWER**: hello', 'some_file') == 1
    assert jmt.validate_markdown_tags(jcxt, 'bla  **ANSWER**: hello', 'some_file') == 0
    

    
def test_preprocessor_sol():
    jm = make_jm()
    import conf
    jmt.init(jm, conf)
    
    
    nb_fn = '_test/test-chapter/nb-sol.ipynb'
    
    resources = make_nb_resources(nb_fn)

    d = '_build/test/.doctrees/nbsphinx/'
    if not os.path.isdir(d):
        os.makedirs(d)

    exp = nbsphinx.Exporter()

    nb_orig = nbformat.read(nb_fn, nbformat.NO_CONVERT)
    
    purged_count = 0
    stripped_count = 0
    for cell in nb_orig.cells:        
        
        if 'stripped!8' in cell.source:
            stripped_count += 1
        if 'purged!9' in cell.source:
            purged_count += 1
                
    assert purged_count == 1    
    assert stripped_count == 1
    
        
    rst_str, new_res = exp.from_notebook_node(nb_orig, resources)
        
    stripped_count = 0
    for cell in nb_orig.cells: 
        if 'stripped!8' in cell.source:
            stripped_count += 1        
            assert not 'purged!9' in cell.source
    assert stripped_count == 1

def test_preprocessor_force():
    jm = make_jm()
    import conf
    jmt.init(jm, conf)
    
    
    nb_fn = '_test/test-chapter/force-preprocess.ipynb'
    
    resources = make_nb_resources(nb_fn)

    d = '_build/test/.doctrees/nbsphinx/'
    if not os.path.isdir(d):
        os.makedirs(d)

    exp = nbsphinx.Exporter()

    nb_orig = nbformat.read(nb_fn, nbformat.NO_CONVERT)
    
    assert 'stripped!' in nb_orig.cells[2].source
    assert 'purged!' in nb_orig.cells[3].source
    
    rst_str, new_res = exp.from_notebook_node(nb_orig, resources)
        
    
    stripped_count = 0
    for cell in nb_orig.cells: 
        if 'stripped!' in cell.source:
            stripped_count += 1                    
        assert '#jupman-strip' not in cell.source 
        assert '#jupman-preprocess' not in cell.source
        assert 'purged!' not in cell.source        
    
    assert stripped_count == 1   # should be in the solution cell
    
def test_preprocessor_normal():
    jm = make_jm()
    import conf
    jmt.init(jm, conf)
    
    nb_fn = '_test/test-chapter/replacements.ipynb'
    
    resources = make_nb_resources(nb_fn)

    d = '_build/test/.doctrees/nbsphinx/'
    if not os.path.isdir(d):
        os.makedirs(d)

    exp = nbsphinx.Exporter()

    nb_orig = nbformat.read(nb_fn, nbformat.NO_CONVERT)
    
    assert 'stay!' in nb_orig.cells[10].source    
    
    nb_new, new_res = exp.from_notebook_node(nb_orig, resources)
    
    assert 'stay!' in nb_orig.cells[10].source            
    
def test_FileKinds_parse():
    """ @since 3.6
    """
    
    # TODO can't detect exercise
    assert FileKinds.parse('my_tutorial.py') == (FileKinds.OTHER, 'my_tutorial', '', 'py')
    
    assert FileKinds.parse('my_tutorial_sol.py') == (FileKinds.SOLUTION, 'my_tutorial', '_sol', 'py')
    assert FileKinds.parse('my_tutorial_chal_sol.py') == (FileKinds.CHALLENGE_SOLUTION, 'my_tutorial', '_chal_sol', 'py')
    
    # TODO can't detect challenge
    assert FileKinds.parse('my_tutorial_chal.py') == (FileKinds.OTHER, 'my_tutorial', '_chal', 'py')
    assert FileKinds.parse('my_tutorial_test.py') == (FileKinds.TEST, 'my_tutorial', '_test', 'py')
    
    #TODO can't detect exercise
    assert FileKinds.parse('my-tutorial.ipynb') == (FileKinds.OTHER, 'my-tutorial', '', 'ipynb')
    
    assert FileKinds.parse('my-tutorial-sol.ipynb') == (FileKinds.SOLUTION, 'my-tutorial', '-sol', 'ipynb')
    assert FileKinds.parse('my-tutorial-chal-sol.ipynb') == (FileKinds.CHALLENGE_SOLUTION, 'my-tutorial', '-chal-sol','ipynb')
    
    # TODO can't detect challenge
    assert FileKinds.parse('my-tutorial-chal.ipynb') == (FileKinds.OTHER, 'my-tutorial', '-chal','ipynb')
    
    #as of 3.6 we don't support notebooks tests
    assert FileKinds.parse('my-tutorial-test.ipynb') == (FileKinds.OTHER, 'my-tutorial-test', '', 'ipynb')
    
    assert FileKinds.parse('some-data.csv') == (FileKinds.OTHER, 'some-data', '','csv')
    
    
    assert FileKinds.parse('my_tutorial_sol.py') == (FileKinds.SOLUTION, 'my_tutorial', '_sol', 'py')
    assert FileKinds.parse('my_tutorial_chal_sol.py') == (FileKinds.CHALLENGE_SOLUTION, 'my_tutorial', '_chal_sol', 'py')    

def test_FileKinds_detect():
    """ @since 3.6
    """
    #TODO a parametric test linked to parse would be much better
    assert FileKinds.detect('my_tutorial_sol.py') == FileKinds.SOLUTION
    assert FileKinds.detect('my_tutorial_chal_sol.py') == FileKinds.CHALLENGE_SOLUTION


def test_expr_matcher():    
    """ @since 3.6
    """

    P = jmt.EXPR_PATTERN
    assert P.match("_JUPMAN_.a").group(0) == "_JUPMAN_.a"
    assert P.match("_JUPMAN_._a") == None    
    # currently not supporting fields that start with _ so we can have _END_, but with a better regex this test may fail
    assert P.match("_JUPMAN_.a._b").group(0) == "_JUPMAN_.a"    
    assert P.match("_JUPMAN_.") == None    
    assert P.match("_JUPMAN_") == None    
    assert P.match("_JUPMAN_.a.b").group(0) == "_JUPMAN_.a.b"
    assert P.match("_JUPMAN_.ab.b").group(0) == "_JUPMAN_.ab.b"
    assert P.match("_JUPMAN_.a.bc").group(0) == "_JUPMAN_.a.bc"    
    assert P.match("_JUPMAN_.7a") == None
    assert P.match("_JUPMAN_.a7").group(0) == "_JUPMAN_.a7"    
    assert P.match("_JUPMAN_.a._END_.b").group(0) == "_JUPMAN_.a._END_"
    assert P.match("_JUPMAN_.a.b._END_").group(0) == "_JUPMAN_.a.b._END_"    
    assert P.match("_JUPMAN_.a.b._END_.cd").group(0) == "_JUPMAN_.a.b._END_"        
    assert P.match("_JUPMAN_.f()").group(0) == "_JUPMAN_.f()"    
    assert P.match("_JUPMAN_.c.ga()").group(0) == "_JUPMAN_.c.ga()"        
    assert P.match("_JUPMAN_.f(3)").group(0) == "_JUPMAN_.f(3)"
    assert P.match("_JUPMAN_.f(2,5,1)").group(0) == "_JUPMAN_.f(2,5,1)"      
    # chaining is not supported, maybe it should refuse/warn but we don't care
    assert P.match("_JUPMAN_.f().g()").group(0) == "_JUPMAN_.f()"
    assert P.match("_JUPMAN_.f()._END_.g()").group(0) == "_JUPMAN_.f()"
    assert P.match("_JUPMAN_.f()._END_.g()").group(0) == "_JUPMAN_.f()"  
    
    
    assert [m.group(0) for m in P.finditer("  _JUPMAN_.a CIAO_JUPMAN_.b.c HELLO ")] == ["_JUPMAN_.a", "_JUPMAN_.b.c"]
    
    assert [m.group(0) for m in P.finditer("Z_JUPMAN_.a _JUPMAN_.b.c Q")] == ["_JUPMAN_.a", "_JUPMAN_.b.c"]    
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a'_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a\t_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a\n_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a]_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a)_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a\"_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]    
    assert [m.group(0) for m in P.finditer("  _JUPMAN_.aZ_JUPMAN_.b")] == ["_JUPMAN_.aZ_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("  _JUPMAN_.a._END__JUPMAN_.b")] == ["_JUPMAN_.a._END_","_JUPMAN_.b"]    
    assert [m.group(0) for m in P.finditer("  _JUPMAN_.a()_JUPMAN_.b")] == ["_JUPMAN_.a()", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("  _JUPMAN_.a()Z_JUPMAN_.b")] == ["_JUPMAN_.a()", "_JUPMAN_.b"]            
    
    
    
def test_replace_templates():
    """ @since 3.6
    """
    
    class C:
        pass
            
    def mkcxt():
        ret = make_jupman_context()
        ret.website = True
        return ret
    
    jcxt = mkcxt();  jcxt.a = 7
    assert jmt.replace_templates(jcxt, "_JUPMAN_.a") == "7"    
    
    jcxt = mkcxt();  
    assert jmt.replace_templates(jcxt, "_JUPMAN_.") == "_JUPMAN_."
    jcxt = mkcxt();  
    assert jmt.replace_templates(jcxt, "_JUPMAN_") == "_JUPMAN_"
    jcxt = mkcxt();  # stuff not defined
    assert jmt.replace_templates(jcxt, "_JUPMAN_.a.b") == "_JUPMAN_.a.b"
    
    jcxt = mkcxt();  jcxt.a = C();  jcxt.a.b = 3   
    assert jmt.replace_templates(jcxt, "_JUPMAN_.a.b") == "3"
    
    jcxt = mkcxt();  jcxt.ab = C();  jcxt.ab.b = 9
    assert jmt.replace_templates(jcxt, "_JUPMAN_.ab.b") == "9"
    jcxt = mkcxt();  jcxt.bc = 2;  jcxt.bc = 2
    assert jmt.replace_templates(jcxt, "_JUPMAN_.a.bc") == "_JUPMAN_.a.bc"
    jcxt = mkcxt();  
    assert jmt.replace_templates(jcxt, "_JUPMAN_.7a") == "_JUPMAN_.7a"
    jcxt = mkcxt();  jcxt.a7 = 4
    assert jmt.replace_templates(jcxt, "_JUPMAN_.a7") == "4"    
    
    jcxt = mkcxt();  jcxt.a = 'x'
    assert jmt.replace_templates(jcxt, "_JUPMAN_.a._END_.b") == "x.b"
    jcxt = mkcxt();  jcxt.a = C(); jcxt.a.b = 'x'
    assert jmt.replace_templates(jcxt, "_JUPMAN_.a.b._END_") == "x"
    jcxt = mkcxt();  jcxt.a = C(); jcxt.a.b = 'x'
    assert jmt.replace_templates(jcxt, "_JUPMAN_.a.b._END_.cd") == "x.cd"    
    
    jcxt = mkcxt();  jcxt.f = lambda xjc: "hi"  
    assert jmt.replace_templates(jcxt, "_JUPMAN_.f()") == "hi"    
    jcxt = mkcxt();  jcxt.c = C(); jcxt.c.ga = lambda xjc: "hello"   
    assert jmt.replace_templates(jcxt, "_JUPMAN_.c.ga()") == "hello"    
    # no more than one parameter (for now)
    jcxt = mkcxt();  jcxt.f = lambda xjc, y: "hello"  
    assert jmt.replace_templates(jcxt, "_JUPMAN_.f(3)") == "_JUPMAN_.f(3)"
    assert jmt.replace_templates(jcxt, "_JUPMAN_.f(2,5,1)") == "_JUPMAN_.f(2,5,1)"
    # chaining is not supported, maybe it should refuse/warn but we don't care
    jcxt = mkcxt();  jcxt.f = lambda xjc: "hi";  jcxt.g = lambda xjc: "hello"; 
    assert jmt.replace_templates(jcxt, "_JUPMAN_.f().g()") == "hi.g()"  
        
     
def test_common_files_maps():
    """ @since 3.6
    """
            
    jcxt = JupmanContext(make_sphinx_config(), '_test/test_chapter/nb-sol.ipynb', True, '')        
    
    with pytest.raises(JupmanError):
        rel_paths, patterns = jmt._common_files_maps(jcxt, 'prova.zip')
    
    jcxt.jm.chapter_files.append(r'_test/test-chapter/**/*pic?.png')
    
    rel_paths, patterns = jmt._common_files_maps(jcxt, 'prova')
    
    print(rel_paths)
    print(patterns)
    
    assert 'jupman.py' in  rel_paths
    assert '_test/test-chapter/img/pic1.png' in rel_paths
    assert '_test/test-chapter/img/more/pic2.png' in rel_paths
    assert ('^(jupman.py)$', 'prova/jupman.py') in  patterns
    assert ('^(_test/test-chapter/img/pic1.png)$', 'prova/_test/test-chapter/img/pic1.png') in patterns
    assert ('^(_test/test-chapter/img/more/pic2.png)$', 'prova/_test/test-chapter/img/more/pic2.png') in patterns
    assert ('^(_test/test-chapter/img/more/pic3.png)$', 'prova/_test/test-chapter/img/more/pic3.png') in patterns           
  
  


def test_zip_folder_test_chapter():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/test-chapter/nb-sol.ipynb', True, '')    
    jcxt.jpre_dest_filepath = '_test/test-chapter/nb.ipynb'
   
    jcxt.jm.chapter_files = ['jupman.py', 
                        'my_lib.py', 
                        '_static/img/cc-by.png', 
                        '_static/js/jupman.js',  
                        '_static/css/jupman.css',                     
                        '_static/js/toc.js',
                        '_static/js/pytutor-embed.bundle.min.js']    
        
    jmt.zip_folder(jcxt, '_test/test-chapter', lambda x : 'test-chapter')
    
    zip_filepath = f"{jcxt.jm.generated}/test-chapter.zip"
    
    from pathlib import Path
    shrinked_zip_files = []
    import zipfile
    with zipfile.ZipFile(zip_filepath) as zf:        
        filepaths = zf.namelist()
        print(filepaths)
        
    
        common  = ['test-chapter/' + cf for cf in jcxt.jm.chapter_files]
        local = [
            'test-chapter/force-preprocess.ipynb', 
            'test-chapter/my_chal.py', 
            'test-chapter/my_chal_test.py', 
            'test-chapter/nb-sol.ipynb', 
            'test-chapter/nb.ipynb', 
            'test-chapter/nb2-chal.ipynb', 
            'test-chapter/population.csv', 
            'test-chapter/replacements.ipynb', 
            'test-chapter/script.py', 
            'test-chapter/some.py', 
            'test-chapter/some_sol.py', 
            'test-chapter/some_test.py', 
            'test-chapter/extra/whatever.pdf', 
            'test-chapter/extra/nested/other.csv', 
            'test-chapter/extra/nested/something.txt', 
            'test-chapter/img/pic1.png', 
            'test-chapter/img/more/pic2.png', 
            'test-chapter/img/more/pic3.png'
        ]
        
        for p in common:
            assert p in filepaths

        for p in local:
            assert p in filepaths

        cl = common + local
        for p in filepaths:
            assert p in cl
    
    
    
