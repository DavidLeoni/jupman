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

from common_test import clean, make_jupman_context, make_sphinx_config, make_jm, make_nb_resources,  tconf
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

class MockSphinx:
    def add_config_value(self, a,b,c):
        pass
    def add_transform(self, a):
        pass
    def add_javascript(self, a):
        pass
    def add_stylesheet(self, a):
        pass


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


def test_is_zip_ignored():
    jcxt = make_jupman_context()    
    assert jmt.is_zip_ignored(jcxt, '.ipynb_checkpoints')
    assert jmt.is_zip_ignored(jcxt, 'prova/.ipynb_checkpoints')
    assert jmt.is_zip_ignored(jcxt, 'prova/__pycache__')
    assert not jmt.is_zip_ignored(jcxt, 'good')
    assert not jmt.is_zip_ignored(jcxt, 'very/good')
    

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
    


    
    


def test_setup(tconf):
        
    mockapp = MockSphinx()
        
    tconf.setup(mockapp)
    # if so tests run smoothly also on non-jupman projects
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
            
    jcxt = JupmanContext(make_sphinx_config(), '_test/test_chapter/nb-sol.ipynb', True)        
    
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
    
     
