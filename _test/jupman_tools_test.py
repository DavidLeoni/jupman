import sys
sys.path.append('../')
sys.path.append('.')  # good lord, without this debugging in VSCode doesn't work

#keep it first so we don't get depreation warnings
import jupman_tools as jmt

from hypothesis import given
from pprint import pprint
from hypothesis.strategies import text
from jupman_tools import ignore_spaces, tag_regex, JupmanConfig, SphinxConfig, JupmanContext
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

from common_test import * 
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
    assert jmt.uproot('_test/test-chapter/data/pop.csv') == '../../../'
    # this is supposed to be a directory
    assert jmt.uproot('_test/non-existing') == '../../'
    assert jmt.uproot('_static/img') == '../../'
    assert jmt.uproot('_static/img/cc-by.png') == '../../'
    assert jmt.uproot('_static/img/non-existing') == '../../../'

def test_replace_sysrel():

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


def test_replace_html_rel():
    """ @since 3.5.4
    """
    
    # note inside it calls uproot, needs this to be run from project root
    assert jmt.replace_html_rel('<a href="../_static/img/hello.png">', '_test/jupman_tools_test.py') \
           == '<a href="_static/img/hello.png">'
    assert jmt.replace_html_rel('<a target="_blank" href="../_static/img/hello.png">', '_test/jupman_tools_test.py') \
           == '<a target="_blank" href="_static/img/hello.png">'       
    assert jmt.replace_html_rel('<img src="../_static/img/hello.png">', '_test/jupman_tools_test.py') \
           == '<img src="_static/img/hello.png">'
    assert jmt.replace_html_rel('<img alt="bla" src="../_static/img/hello.png">', '_test/jupman_tools_test.py') \
           == '<img alt="bla" src="_static/img/hello.png">'
       
    assert jmt.replace_html_rel('A B <img alt="cc-by-1243" src="../_static/img/cc-by.png"> C D', '_test/jupman_tools_test.py') \
           == 'A B <img alt="cc-by-1243" src="_static/img/cc-by.png"> C D'

def test_copy_chapter():
    clean()
    
    jcxt = make_jupman_context()    
    os.makedirs(jcxt.jm.build)
    dest_dir = os.path.join(jcxt.jm.build, 'test-chapter')
    jmt.copy_code(jcxt, '_test/test-chapter',
                  dest_dir,
                  copy_solutions=True)    

    assert os.path.isdir(dest_dir)

    replacements_fn = os.path.join(dest_dir, 'replacements.ipynb')
    assert os.path.isfile(replacements_fn)

    nb_node = nbformat.read(replacements_fn, nbformat.NO_CONVERT)

    # markdown                             
    assert '[some link](index.ipynb)' in nb_node.cells[1].source
    assert '![some link](_static/img/cc-by.png)' in nb_node.cells[2].source
    assert '[some link](data/pop.csv)' in nb_node.cells[3].source

    assert '<a href="index.ipynb" target="_blank">a link</a>' in nb_node.cells[4].source
    
    assert '<img src="_static/img/cc-by.png">' in nb_node.cells[5].source
    assert '<a href="data/pop.csv">a link</a>' in nb_node.cells[6].source
    
    assert '<a href="index.ipynb">a link</a>' in nb_node.cells[7].source

    assert '<img src="_static/img/cc-by.png">' in nb_node.cells[8].source

    assert '<a href="data/pop.csv">a link</a>' in nb_node.cells[9].source

    assert '# Python\nimport jupman' in nb_node.cells[10].source
    assert '#jupman-raise' in nb_node.cells[10].source
    assert 'stay!' in nb_node.cells[10].source

    assert '<a href="index.html">a link</a>' in nb_node.cells[11].source
    
    assert '<a href="https://jupman.softpython.org">a link</a>' in nb_node.cells[12].source
    
    assert '<img alt="bla13" src="_static/img/cc-by.png">' in nb_node.cells[13].source
    
    assert '<a target="_blank" href="index.ipynb">a link</a>' in nb_node.cells[14].source
    
    assert '<a target="_blank" href="https://jupman.softpython.org">a link</a>' in nb_node.cells[15].source

    assert 'replacements.ipynb' in nb_node.cells[16].source
    assert jcxt.jm.manual in nb_node.cells[16].source
    assert jcxt.author in nb_node.cells[16].source
        
    assert 'replacements.ipynb' in nb_node.cells[17].source
    assert jcxt.jm.manual in nb_node.cells[17].source
    assert nb_node.cells[17].source.count(jcxt.author) == 2
        
    assert 'replacements.ipynb' in nb_node.cells[18].source
    assert jcxt.jm.manual in nb_node.cells[18].source
    assert jcxt.author in nb_node.cells[18].source
            
    assert 'replacements.ipynb' in nb_node.cells[19].source
    assert jcxt.jm.manual in nb_node.cells[19].source
    assert jcxt.author in nb_node.cells[19].source
    

    py_fn = os.path.join(dest_dir, 'file.py')
    assert os.path.isfile(py_fn)

    with open(py_fn, encoding='utf-8') as py_f:
        py_code = py_f.read()
        assert '# Python\nimport jupman' in py_code
        assert '#jupman-raise' in py_code

    test_fn = os.path.join(dest_dir, 'some_test.py')
    assert os.path.isfile(test_fn)

    with open(test_fn, encoding='utf-8') as test_f:
        test_code = test_f.read()
        assert 'some_sol' not in test_code
        assert '# Python\nimport some\nimport jupman' in test_code
        assert '#jupman-raise' in test_code

    sol_fn = os.path.join(dest_dir, 'some_sol.py')
    assert os.path.isfile(sol_fn)

    with open(sol_fn, encoding='utf-8') as py_sol_f:
        sol_code = py_sol_f.read()
        assert '# Python\nimport jupman' in sol_code
        assert '#jupman-raise' not in sol_code
        assert '#jupman-strip' not in sol_code
        assert '#jupman-purge' not in sol_code
        assert 'stripped!' in sol_code
        assert 'purged!' not in sol_code        
        assert "# work!\n\nprint('hi')" in sol_code

    ex_fn = os.path.join(dest_dir, 'some.py')
    assert os.path.isfile(ex_fn)

    with open(ex_fn, encoding='utf-8') as py_ex_f:
        py_ex_code = py_ex_f.read()
        assert '# Python\nimport jupman' in py_ex_code
        assert '#jupman-raise' not in py_ex_code
        assert '# work!\nraise' in py_ex_code

    # nb_ex ----------------------------
    nb_ex_fn = os.path.join(dest_dir, 'nb.ipynb')
    assert os.path.isfile(nb_ex_fn)

    nb_ex = nbformat.read(nb_ex_fn, nbformat.NO_CONVERT)
    
    #pprint(nb_ex)
    assert "# Notebook EXERCISES" in nb_ex.cells[0].source
    assert "#before\nraise" in nb_ex.cells[1].source
    assert nb_ex.cells[2].source == ""   # SOLUTION strips everything
    assert nb_ex.cells[3].source.strip() == "# 3\n# write here"    # write here strips afterwards
    #4 question
    #5 answer: must begin with answer and strips everything after
    assert nb_ex.cells[5].source == '**ANSWER**:\n'
    #6 write here 
    assert nb_ex.cells[6].source == 'x = 6\n# write here fast please\n\n'
    assert nb_ex.cells[7].source == '' # SOLUTION strips everything
    assert nb_ex.cells[8].source == 'x = 8\n\n# after'  # jupman-strip  strips everything inside exercises
    assert nb_ex.cells[9].source == 'x = 9\n\n# after'  # jupman-purge everything inside exercises 
    assert '#jupman-strip' not in nb_ex.cells[10].source   
    assert '#jupman-purge' not in nb_ex.cells[10].source   
    assert nb_ex.cells[11].source == ''
    assert 'purged!11' in nb_ex.cells[11].outputs[0]['text']
    
    
    assert '#jupman-purge-output' not in nb_ex.cells[12].source
    assert '-output' not in nb_ex.cells[12].source
    assert 'purged!12' in nb_ex.cells[12].source
    assert nb_ex.cells[12].outputs == []
    
    assert nb_ex.cells[13].source == ''    
    assert nb_ex.cells[13].outputs == []
    assert nb_ex.cells[13].metadata['nbsphinx'] == 'hidden'
    
    

    # nb_sol --------------------
    nb_sol_fn = os.path.join(dest_dir, 'nb-sol.ipynb')
    nb_sol = nbformat.read(nb_sol_fn, nbformat.NO_CONVERT) 
    assert 'stripped!' in nb_sol.cells[8].source   # jupman-strip  strips everything inside exercises
    assert '#jupman-strip' not in nb_sol.cells[8].source   
    assert 'purged!' not in  nb_sol.cells[9].source  # jupman-purge  strips everything also in solutions    
    assert '#jupman-purge' not in nb_sol.cells[9].source           
    
    assert '#jupman-strip' not in nb_sol.cells[10].source   
    assert '#jupman-purge' not in nb_sol.cells[10].source       
    assert 'stripped!' in nb_sol.cells[10].source
    assert 'purged!10' not in nb_sol.cells[10].source
    
    assert nb_sol.cells[11].source == ''
    assert 'purged!11' in nb_sol.cells[11].outputs[0]['text']
    
    
    assert '#jupman-purge-output' not in nb_sol.cells[12].source
    assert '-output' not in nb_sol.cells[12].source
    assert 'purged!12' in nb_sol.cells[12].source
    assert nb_sol.cells[12].outputs == []
    
    assert nb_sol.cells[13].source == ''    
    assert nb_sol.cells[13].outputs == []
    assert nb_sol.cells[13].metadata['nbsphinx'] == 'hidden'

    # nb_sol_web --------------------
    nb_sol_fn = os.path.join(dest_dir, 'nb-sol.ipynb')
    nb_sol_web = nbformat.read(nb_sol_fn, nbformat.NO_CONVERT)

    jcxt = JupmanContext(make_sphinx_config(), os.path.abspath(nb_sol_fn), True)

    jmt._sol_nb_to_ex(jcxt, nb_sol_web)
    
    stripped8 = 0
    stripped10 = 0
    for cell in nb_sol_web.cells:
        if 'stripped!8' in cell.source:
            stripped8 += 1
        if 'stripped!10' in cell.source:
            stripped10 += 1    
        assert 'purged!9' not in cell.source
        assert 'purged!10' not in cell.source
        assert 'purged!11' not in cell.source
        if getattr(cell, 'outputs', None):
            assert 'purged!12' not in cell.outputs[0]['text']
        assert 'purged!13' not in cell.source
        if getattr(cell, 'outputs', None):
            assert 'purged!13' not in cell.outputs[0]['text']
    assert stripped8 == 1
    assert stripped10 == 1

    # chal --------------------
    py_chal_sol_fn = os.path.join(dest_dir, 'my_chal_sol.py')    
    assert not os.path.isfile(py_chal_sol_fn)
    py_chal_fn = os.path.join(dest_dir, 'my_chal.py')
    assert os.path.isfile(py_chal_fn)

    py_chal_test_fn = os.path.join(dest_dir, 'my_chal_test.py')
    assert os.path.isfile(py_chal_test_fn)
    with open(py_chal_test_fn) as py_chal_test_f: 
        py_chal_test_code = py_chal_test_f.read()
        assert 'from my_chal import *' in py_chal_test_code

    nb_chal_ex_fn = os.path.join(dest_dir, 'nb-chal.ipynb')    
    assert os.path.isfile(nb_chal_ex_fn)
    nb_chal_sol_fn = os.path.join(dest_dir, 'nb-chal-sol.ipynb')
    assert not os.path.isfile(nb_chal_sol_fn)

    nb_chal_ex = nbformat.read(nb_chal_ex_fn, nbformat.NO_CONVERT)

    assert jcxt.jm.ipynb_solutions not in nb_chal_ex.cells[1].source
    


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
    #print(p)
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
    
        
    nb_new, new_res = exp.from_notebook_node(nb_orig, resources)
        
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
    
    nb_new, new_res = exp.from_notebook_node(nb_orig, resources)
        
    stripped_count = 0
    for cell in nb_orig.cells: 
        if 'stripped!' in cell.source:
            stripped_count += 1                    
        assert '#jupman-strip' not in cell.source 
        assert '#jupman-preprocess' not in cell.source
        assert 'purged!' not in cell.source        
    
    assert stripped_count == 1
    
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
    
def test_expr_matcher():    

    P = jmt.EXPR_PATTERN
    assert P.match("_JUPMAN_.a").group(0) == "_JUPMAN_.a"    
    assert P.match("_JUPMAN_.") == None    
    assert P.match("_JUPMAN_") == None    
    assert P.match("_JUPMAN_.a.b").group(0) == "_JUPMAN_.a.b"
    assert P.match("_JUPMAN_.ab.b").group(0) == "_JUPMAN_.ab.b"
    assert P.match("_JUPMAN_.a.bc").group(0) == "_JUPMAN_.a.bc"
    assert P.match("_JUPMAN_.7a") == None
    assert P.match("_JUPMAN_.a7").group(0) == "_JUPMAN_.a7"    
    assert P.match("_JUPMAN_.f()").group(0) == "_JUPMAN_.f()"    
    assert P.match("_JUPMAN_.c.ga()").group(0) == "_JUPMAN_.c.ga()"        
    assert P.match("_JUPMAN_.f(3)").group(0) == "_JUPMAN_.f(3)"
    assert P.match("_JUPMAN_.f(2,5,1)").group(0) == "_JUPMAN_.f(2,5,1)"      
    # chaining is not supported, maybe it should refuse/warn but we don't care
    assert P.match("_JUPMAN_.f().g()").group(0) == "_JUPMAN_.f()"  
    
    
    assert [m.group(0) for m in P.finditer("  _JUPMAN_.a CIAO_JUPMAN_.b.c HELLO ")] == ["_JUPMAN_.a", "_JUPMAN_.b.c"]
    
    assert [m.group(0) for m in P.finditer("Z_JUPMAN_.a _JUPMAN_.b.c Q")] == ["_JUPMAN_.a", "_JUPMAN_.b.c"]    
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a'_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a\t_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a\n_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a]_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a)_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("_JUPMAN_.a\"_JUPMAN_.b")] == ["_JUPMAN_.a", "_JUPMAN_.b"]
    # a non-character separator is always necessary, in future if we improve the regex this test may fail 
    assert [m.group(0) for m in P.finditer("  _JUPMAN_.aZ_JUPMAN_.b")] == ["_JUPMAN_.aZ_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("  _JUPMAN_.a()_JUPMAN_.b")] == ["_JUPMAN_.a()", "_JUPMAN_.b"]
    assert [m.group(0) for m in P.finditer("  _JUPMAN_.a()Z_JUPMAN_.b")] == ["_JUPMAN_.a()", "_JUPMAN_.b"]
    
    
    
def test_replace_templates():
    
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
        
     
