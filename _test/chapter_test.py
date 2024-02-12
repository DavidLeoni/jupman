import sys
sys.path.append('../')
sys.path.append('.')  # good lord, without this debugging in VSCode doesn't work

#keep it first so we don't get deprecation warnings
import jupman_tools as jmt
import os
import nbformat
from jupman_tools import JupmanContext
from common_test import clean, make_jupman_context, make_sphinx_config, tconf
import pytest 
from jupman_tools import debug



@pytest.fixture(scope="module")
def dest_dir():
    
    clean()
    
    jcxt = make_jupman_context()    
    os.makedirs(jcxt.jm.build)
    ret_dir = os.path.join(jcxt.jm.build, 'test-chapter')
    jmt.copy_code(jcxt, '_test/test-chapter',
                  ret_dir,
                  copy_solutions=True)    
    
    assert os.path.isdir(ret_dir)
    
    return ret_dir
    

def test_copy_chapter_replacements(dest_dir):
    
    replacements_fn = os.path.join(dest_dir, 'replacements.ipynb')
    jcxt = JupmanContext(make_sphinx_config(), replacements_fn, False, '')
    
    assert os.path.isfile(replacements_fn)

    nb_repl = nbformat.read(replacements_fn, nbformat.NO_CONVERT)


    # markdown                             
    assert '[some link](index.ipynb)' in nb_repl.cells[1].source
    assert '![some link](_static/img/cc-by.png)' in nb_repl.cells[2].source
    assert '[some link](data/pop.csv)' in nb_repl.cells[3].source    

    assert '<a href="index.ipynb" target="_blank">a link</a>' in nb_repl.cells[4].source
    
    assert '<img src="_static/img/cc-by.png">' in nb_repl.cells[5].source
    assert '<a href="data/pop.csv">a link</a>' in nb_repl.cells[6].source
    
    assert '<a href="index.ipynb">a link</a>' in nb_repl.cells[7].source

    assert '<img src="_static/img/cc-by.png">' in nb_repl.cells[8].source

    assert '<a href="data/pop.csv">a link</a>' in nb_repl.cells[9].source

    assert '# Python\nimport jupman' in nb_repl.cells[10].source
    assert '#jupman-raise' in nb_repl.cells[10].source
    assert 'stay!' in nb_repl.cells[10].source

    assert '<a href="index.html">a link</a>' in nb_repl.cells[11].source
    
    assert '<a href="https://jupman.softpython.org">a link</a>' in nb_repl.cells[12].source
    
    assert '<img alt="bla13" src="_static/img/cc-by.png">' in nb_repl.cells[13].source
    
    assert '<a target="_blank" href="index.html">a link</a>' in nb_repl.cells[14].source
    
    assert '<a target="_blank" href="https://jupman.softpython.org">a link</a>' in nb_repl.cells[15].source
    
    assert  """<style>\n@import _static/css/ab.css;\n</style>""" in nb_repl.cells[16].source

    assert '<style> @import "_static/css/cd.css" </style>' in  nb_repl.cells[16].source
        
    assert '<script src="static/js/ab.js" type="application/javascript"></script>' in nb_repl.cells[17].source 
    assert '<script src="static/js/cd.js" type="application/javascript" defer="defer"> </script>' in nb_repl.cells[17].source         

    assert nb_repl.cells[18].source.count('replacements.ipynb') == 2
    assert jcxt.jm.manual in nb_repl.cells[18].source
    assert jcxt.author in nb_repl.cells[18].source
        
    assert nb_repl.cells[19].source.count('replacements.ipynb') == 2
    assert jcxt.jm.manual in nb_repl.cells[19].source
    assert nb_repl.cells[19].source.count(jcxt.author) == 2
        
    assert nb_repl.cells[20].source.count('replacements.ipynb') == 2
    assert jcxt.jm.manual in nb_repl.cells[20].source
    assert jcxt.author in nb_repl.cells[20].source
            
    assert nb_repl.cells[21].source.count('replacements.ipynb') == 2
    assert jcxt.jm.manual in nb_repl.cells[21].source
    assert jcxt.author in nb_repl.cells[21].source       


def test_copy_chapter_py_files(dest_dir):

    py_fn = os.path.join(dest_dir, 'script.py')
    jcxt = JupmanContext(make_sphinx_config(), py_fn, False, '')
    assert os.path.isfile(py_fn)

    with open(py_fn, encoding='utf-8') as py_f:
        py_code = py_f.read()
        assert '# Python\nimport jupman' in py_code
        assert '#jupman-raise' in py_code
        assert py_code.count('script.py') == 2
        assert jcxt.jm.manual in py_code
        assert jcxt.author in py_code        
        

    test_fn = os.path.join(dest_dir, 'some_test.py')
    jcxt = JupmanContext(make_sphinx_config(), test_fn, False, '')
    assert os.path.isfile(test_fn)

    with open(test_fn, encoding='utf-8') as test_f:
        test_code = test_f.read()
        assert 'some_sol' not in test_code
        assert '# Python\nimport some\nimport jupman' in test_code
        assert '#jupman-raise' in test_code
        assert test_code.count('some_test.py') == 2
        assert jcxt.jm.manual in test_code
        assert jcxt.author in test_code        

    sol_fn = os.path.join(dest_dir, 'some_sol.py')
    jcxt = JupmanContext(make_sphinx_config(), sol_fn, False, '')
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
        assert sol_code.count('some_sol.py') == 2
        assert jcxt.jm.manual in sol_code
        assert jcxt.author in sol_code

    ex_fn = os.path.join(dest_dir, 'some.py')
    assert os.path.isfile(ex_fn)

    with open(ex_fn, encoding='utf-8') as py_ex_f:
        py_ex_code = py_ex_f.read()
        assert '# Python\nimport jupman' in py_ex_code
        assert '#jupman-raise' not in py_ex_code
        assert '# work!\nraise' in py_ex_code
        assert 'some_sol.py' in py_ex_code
        assert 'some.py' in py_ex_code
        assert jcxt.jm.manual in py_ex_code
        assert jcxt.author in py_ex_code        
    

def test_copy_chapter_exercises(dest_dir):

    nb_ex_fn = os.path.join(dest_dir, 'nb.ipynb')
    jcxt = JupmanContext(make_sphinx_config(), nb_ex_fn, False, '')
    
    assert os.path.isfile(nb_ex_fn)

    nb_ex = nbformat.read(nb_ex_fn, nbformat.NO_CONVERT)
    
    
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
    
    assert nb_ex.cells[14].source == """x = 14\nimport jupman"""
    
    assert '<script src=\"_static/js/pytutor-embed.bundle.min.js' in nb_ex.cells[15].outputs[0]['data']['text/html']
    assert  '@import \"_static/css/jupman.css\"' in nb_ex.cells[15].outputs[0]['data']['text/html']
                   
    assert 'nb.ipynb' in nb_ex.cells[16].source
    assert 'nb-sol.ipynb' in nb_ex.cells[16].source
    assert jcxt.jm.manual in nb_ex.cells[16].source
    assert jcxt.author in nb_ex.cells[16].source
        
    assert 'nb.ipynb' in nb_ex.cells[17].source
    assert 'nb-sol.ipynb' in nb_ex.cells[17].source
    assert jcxt.jm.manual in nb_ex.cells[17].source
    assert nb_ex.cells[17].source.count(jcxt.author) == 2
        
    assert 'nb.ipynb' in nb_ex.cells[18].source
    assert 'nb-sol.ipynb' in nb_ex.cells[18].source
    assert jcxt.jm.manual in nb_ex.cells[18].source
    assert jcxt.author in nb_ex.cells[18].source
            
    assert 'nb.ipynb' in nb_ex.cells[19].source
    assert 'nb-sol.ipynb' in nb_ex.cells[19].source
    assert jcxt.jm.manual in nb_ex.cells[19].source
    assert jcxt.author in nb_ex.cells[19].source    


def test_copy_chapter_solution(dest_dir):
    
    nb_sol_fn = os.path.join(dest_dir, 'nb-sol.ipynb')
    jcxt = JupmanContext(make_sphinx_config(), nb_sol_fn, False, '')
    
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
    
    assert '<script src=\"_static/js/pytutor-embed.bundle.min.js' in nb_sol.cells[15].outputs[0]['data']['text/html']
    assert  '@import \"_static/css/jupman.css\"' in nb_sol.cells[15].outputs[0]['data']['text/html']    
    
    assert nb_sol.cells[16].source.count('nb-sol.ipynb') == 2
    assert jcxt.jm.manual in nb_sol.cells[16].source
    assert jcxt.author in nb_sol.cells[16].source
        
    assert nb_sol.cells[17].source.count('nb-sol.ipynb') == 2
    assert jcxt.jm.manual in nb_sol.cells[17].source
    assert nb_sol.cells[17].source.count(jcxt.author) == 2
        
    assert nb_sol.cells[18].source.count('nb-sol.ipynb') == 2
    assert jcxt.jm.manual in nb_sol.cells[18].source
    assert jcxt.author in nb_sol.cells[18].source
            
    assert nb_sol.cells[19].source.count('nb-sol.ipynb') == 2
    assert jcxt.jm.manual in nb_sol.cells[19].source
    assert jcxt.author in nb_sol.cells[19].source    
    

def test_chapter_solution_web(): 

    nb_sol_fn = os.path.join('_test/test-chapter', 'nb-sol.ipynb')
    nb_sol_web = nbformat.read(nb_sol_fn, nbformat.NO_CONVERT)

    jcxt = JupmanContext(make_sphinx_config(), os.path.abspath(nb_sol_fn), True, '')

    jmt._sol_nb_to_ex(jcxt, nb_sol_web)
    
    stripped8 = 0
    stripped10 = 0
    import_jupman = 0
    pytutor_js = 0
    jupman_css = 0
    
    for cell in nb_sol_web.cells:
        if 'stripped!8' in cell.source:
            stripped8 += 1
        if 'stripped!10' in cell.source:
            stripped10 += 1    
        assert 'purged!9' not in cell.source
        assert 'purged!10' not in cell.source
        assert 'purged!11' not in cell.source
        if getattr(cell, 'outputs', None):
            if 'text' in cell.outputs[0]:
                assert 'purged!12' not in cell.outputs[0]['text']
        assert 'purged!13' not in cell.source
        if getattr(cell, 'outputs', None):
            if 'text' in cell.outputs[0]:
                assert 'purged!13' not in cell.outputs[0]['text']
                
        if cell.source == """x = 14\nimport jupman""":
            import_jupman += 1
        
        
        if 'outputs' in cell and len(cell.outputs) > 0 and  'data' in cell.outputs[0]:
            if '<script src="../../_static/js/pytutor-embed.bundle.min.js' in cell.outputs[0]['data']['text/html']:
                pytutor_js += 1
                
        if 'outputs' in cell and len(cell.outputs) > 0 and 'data' in cell.outputs[0]:                        
            if '@import "../../_static/css/jupman.css"' in cell.outputs[0]['data']['text/html']:                
                jupman_css += 1            

        if '16 -' in cell.source:            
            assert cell.source.count('nb-sol.ipynb') == 2
        if '17 -' in cell.source:            
            assert cell.source.count('nb-sol.ipynb') == 2

        #TODO preamble stuff                       
                
    assert stripped8 == 1
    assert stripped10 == 1
    assert import_jupman == 1
    assert pytutor_js == 1            
    assert jupman_css == 1            
    

def test_copy_chapter_challenge(dest_dir):
    
    nb_sol_fn = os.path.join(dest_dir, 'nb-sol.ipynb')

            
    py_chal_sol_fn = os.path.join(dest_dir, 'my_chal_sol.py')    
    assert not os.path.isfile(py_chal_sol_fn)
    py_chal_fn = os.path.join(dest_dir, 'my_chal.py')
    assert os.path.isfile(py_chal_fn)

    py_chal_test_fn = os.path.join(dest_dir, 'my_chal_test.py')
    assert os.path.isfile(py_chal_test_fn)
    with open(py_chal_test_fn) as py_chal_test_f: 
        py_chal_test_code = py_chal_test_f.read()
        assert 'from my_chal import *' in py_chal_test_code

    
    nb_chal_ex_fn = os.path.join(dest_dir, 'nb2-chal.ipynb')    
    jcxt = JupmanContext(make_sphinx_config(), os.path.abspath(nb_chal_ex_fn), True, '')
    assert os.path.isfile(nb_chal_ex_fn)
    nb_chal_sol_fn = os.path.join(dest_dir, 'nb2-chal-sol.ipynb')
    assert not os.path.isfile(nb_chal_sol_fn)

    nb_chal_ex = nbformat.read(nb_chal_ex_fn, nbformat.NO_CONVERT)

    assert jcxt.jm.ipynb_solutions not in nb_chal_ex.cells[1].source
    
