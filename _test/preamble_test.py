import sys
sys.path.append('../')
sys.path.append('.')  # good lord, without this debugging in VSCode doesn't work

#keep it first so we don't get depreation warnings
import jupman_tools as jmt
import os
import re
import nbformat

from common_test import clean, make_jupman_context, make_sphinx_config, tconf
import pytest 
from jupman_tools import ignore_spaces, tag_regex, JupmanConfig, SphinxConfig, JupmanContext, JupmanError, JupmanNotFoundError, FileKinds, JupmanPreprocessorError, JupmanEmptyChapterError, JupmanUnsupportedError

from jupman_tools import debug


def test_compare_chapter_files():        
    """ 
        TODO more characters, parametrize
        @since 3.6
    """
    cfw = jmt._chapter_files_weight
    
    assert re.search(cfw[0], 'peppo.ipynb')
    assert not re.search(cfw[0], 'peppo-sol.ipynb')    
        
    assert jmt._compare_chapter_files('a.py', 'a.py') == 0    
    assert jmt._compare_chapter_files('a.py', 'a_sol.py') == -1
    assert jmt._compare_chapter_files('a.py', 'a_test.py') == -1
    assert jmt._compare_chapter_files('a.py', 'a.ipynb') == 1
    assert jmt._compare_chapter_files('a.py', 'a') == -1    
    assert jmt._compare_chapter_files('a_test.py', 'a.py') == 1
    assert jmt._compare_chapter_files('a_test.py', 'a_test.py') == 0    
    assert jmt._compare_chapter_files('a_test.py', 'a_sol.py') == -1
    assert jmt._compare_chapter_files('a_test.py', 'a_test.ipynb') == 1
    assert jmt._compare_chapter_files('a_test.py', 'a') == -1
    assert jmt._compare_chapter_files('a_sol.py', 'a.py') == 1
    assert jmt._compare_chapter_files('a_sol.py', 'a_test.py') == 1
    assert jmt._compare_chapter_files('a_sol.py', 'a_sol.py') == 0
    assert jmt._compare_chapter_files('a_sol.py', 'a_sol.ipynb') == 1
    assert jmt._compare_chapter_files('a_sol.py', 'a') == -1  
    
    assert jmt._compare_chapter_files('a.ipynb', 'a.py') == -1
    assert jmt._compare_chapter_files('a.ipynb', 'a_sol.py') == -1
    assert jmt._compare_chapter_files('a.ipynb', 'a_test.py') == -1
    assert jmt._compare_chapter_files('a.ipynb', 'a.ipynb') == 0
    assert jmt._compare_chapter_files('a.ipynb', 'a') == -1    
    assert jmt._compare_chapter_files('a-test.ipynb', 'a.py') == -1
    assert jmt._compare_chapter_files('a_test.ipynb', 'a_test.py') == -1
    assert jmt._compare_chapter_files('a-test.ipynb', 'a_sol.py') == -1
    assert jmt._compare_chapter_files('a-test.ipynb', 'a-test.ipynb') == 0
    assert jmt._compare_chapter_files('a-test.ipynb', 'a') == -1
    assert jmt._compare_chapter_files('a-sol.ipynb', 'a.py') == -1
    assert jmt._compare_chapter_files('a-sol.ipynb', 'a_test.py') == -1
    assert jmt._compare_chapter_files('a_sol.ipynb', 'a_sol.py') == -1
    assert jmt._compare_chapter_files('a-sol.ipynb', 'a-sol.ipynb') == 0
    assert jmt._compare_chapter_files('a-sol.ipynb', 'a') == -1  

    assert jmt._compare_chapter_files('a', 'a.py') == 1
    assert jmt._compare_chapter_files('a', 'a_sol.py') == 1
    assert jmt._compare_chapter_files('a', 'a_test.py') == 1
    assert jmt._compare_chapter_files('a', 'a.ipynb') == 1
    assert jmt._compare_chapter_files('a', 'a') == 0    
    assert jmt._compare_chapter_files('a-test', 'a.py') == 1
    assert jmt._compare_chapter_files('a_test', 'a_test.py') == 1
    assert jmt._compare_chapter_files('a-test', 'a_sol.py') == 1
    assert jmt._compare_chapter_files('a-test', 'a-test.ipynb') == 1
    assert jmt._compare_chapter_files('a-test', 'a') == 1
    assert jmt._compare_chapter_files('a-sol', 'a.py') == 1
    assert jmt._compare_chapter_files('a-sol', 'a_test.py') == 1
    assert jmt._compare_chapter_files('a_sol', 'a_sol.py') == 1
    assert jmt._compare_chapter_files('a-sol', 'a-sol.ipynb') == 1
    assert jmt._compare_chapter_files('a-sol', 'a') == 1

    
    assert jmt._compare_chapter_files('a', 'a') == 0
    assert jmt._compare_chapter_files('a', 'b') == -1
    assert jmt._compare_chapter_files('b', 'a') == 1


def test_make_preamble_filelist_chap2_one_marked_file():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/chap2-only-one/a.ipynb', True, '') 
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/chap2-only-one', lambda x : 'chap2-only-one')
        
    lst = jmt._make_preamble_filelist(jcxt, 
                                      f"{jcxt.jm.generated}/chap2-only-one.zip",
                                      ['a.ipynb'])
    
    assert lst == [(0, 'chap2-only-one'), 
                        (1,'a.ipynb', '*'),
                        (1,'jupman.py')]


def test_make_preamble_filelist_chap2_unspecified_marked_files():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/chap2-only-one/a.ipynb', True, '') 
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/chap2-only-one', lambda x : 'chap2-only-one')
        
    lst = jmt._make_preamble_filelist(jcxt, 
                                      f"{jcxt.jm.generated}/chap2-only-one.zip")
    
    assert lst == [(0, 'chap2-only-one'), 
                        (1,'a.ipynb', '*'),
                        (1,'jupman.py')]


def test_make_preamble_filelist_chap2_no_marked_files():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/chap2-only-one/a.ipynb', True, '') 
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/chap2-only-one', lambda x : 'chap2-only-one')
        
    lst = jmt._make_preamble_filelist(jcxt, 
                                      f"{jcxt.jm.generated}/chap2-only-one.zip",
                                      [])
    
    assert lst == [(0, 'chap2-only-one'), 
                        (1,'a.ipynb'),
                        (1,'jupman.py')]
    
def test_make_preamble_filelist_chap2_non_existing_dest_file():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/chap2-only-one/WHAT666.ipynb', True, '') 
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/chap2-only-one', lambda x : 'chap2-only-one')

    with pytest.raises(JupmanNotFoundError):        
        lst = jmt._make_preamble_filelist(jcxt,  f"{jcxt.jm.generated}/chap2-only-one.zip")
    

     
def test_make_preamble_filelist_chap2_no_ignored_ipynb():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/chap2-only-one/a.ipynb', True, '') 
    jcxt.jm.chapter_files = ['jupman.py', '_static/js/jupman.js', '_static/img/cc-by.png' ]
    jmt.zip_folder(jcxt, '_test/chap2-only-one', lambda x : 'chap2-only-one')
        
    lst = jmt._make_preamble_filelist(jcxt, 
                                      f"{jcxt.jm.generated}/chap2-only-one.zip",
                                      ignored=[])
    
    assert lst == [(0, 'chap2-only-one'), 
                        (1, '_static'), 
                            (2, 'img'),
                                (3, 'cc-by.png'),
                            (2, 'js'), 
                                (3, 'jupman.js'), 
                        (1,'a.ipynb', '*'),
                        (1,'jupman.py')]

def test_make_preamble_filelist_chap3_non_existing_dest_file():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/chap3-empty/a.ipynb', True, '') 
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/chap3-empty', lambda x : 'chap3-empty')
        
    with pytest.raises(JupmanNotFoundError):
        lst = jmt._make_preamble_filelist(jcxt, 
                                        f"{jcxt.jm.generated}/chap3-empty.zip")
    


def test_make_preamble_filelist_chap3_non_existing_dest_non_existing_marked_file():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/chap3-empty/a.ipynb', True, '') 
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/chap3-empty', lambda x : 'chap3-empty')
        
    with pytest.raises(JupmanNotFoundError):
        lst = jmt._make_preamble_filelist(jcxt, 
                                        f"{jcxt.jm.generated}/chap3-empty.zip",
                                        ['b.ipynb'])
    
         
def test_make_preamble_filelist_chap3_no_ignored_ipynb():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/chap3-empty/a.ipynb', True, '') 
    jcxt.jm.chapter_files = ['jupman.py', '_static/js/jupman.js', '_static/img/cc-by.png' ]
    jmt.zip_folder(jcxt, '_test/chap3-empty', lambda x : 'chap3-empty')
        
    with pytest.raises(JupmanNotFoundError):
        lst = jmt._make_preamble_filelist(jcxt, 
                                        f"{jcxt.jm.generated}/chap3-empty.zip",
                                        [],
                                        [])    



def test_make_preamble_filelist_test_chapter_two_marked_files():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/test-chapter/nb-sol.ipynb', True, '')  
    jcxt.jpre_dest_filepath = '_test/test-chapter/nb.ipynb'
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/test-chapter', lambda x : 'test-chapter')
    
    lst = jmt._make_preamble_filelist(jcxt, 
                                      f"{jcxt.jm.generated}/test-chapter.zip",                                      
                                      marked = ['nb.ipynb', 'population.csv'])
    
    assert lst == [(0, 'test-chapter'),                         
                        (1, 'extra'),                            
                            (2, 'nested'),
                                (3, 'other.csv'),
                                (3, 'something.txt'),                                
                            (2, 'whatever.pdf'),
                        (1, 'force-preprocess.ipynb'),
                        (1, 'nb.ipynb', '*'),                        
                        (1, 'nb-sol.ipynb'),
                        (1, 'nb2-chal.ipynb'),
                        (1, 'replacements.ipynb'),
                        (1, 'my_chal.py'),
                        (1, 'my_chal_test.py'),
                        (1, 'script.py'),
                        (1, 'some.py'),                        
                        (1, 'some_test.py'),
                        (1, 'some_sol.py'),
                        (1, 'population.csv', '*'),
                        (1,'jupman.py') ]
    

def test_make_preamble_filelist_test_chapter_marked_non_dest():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/test-chapter/nb-sol.ipynb', True, '')  
    jcxt.jpre_dest_filepath = '_test/test-chapter/nb.ipynb'
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/test-chapter', lambda x : 'test-chapter')
    
    lst = jmt._make_preamble_filelist(jcxt, 
                                      f"{jcxt.jm.generated}/test-chapter.zip",                                      
                                      marked = ['replacements.ipynb'])
 
    assert lst == [(0, 'test-chapter'),                         
                        (1, 'extra'),                            
                            (2, 'nested'),
                                (3, 'other.csv'),
                                (3, 'something.txt'),                                
                            (2, 'whatever.pdf'),
                        (1, 'force-preprocess.ipynb'),
                        (1, 'nb.ipynb'),                        
                        (1, 'nb-sol.ipynb'),
                        (1, 'nb2-chal.ipynb'),
                        (1, 'replacements.ipynb', '*'),
                        (1, 'my_chal.py'),
                        (1, 'my_chal_test.py'),
                        (1, 'script.py'),
                        (1, 'some.py'),                        
                        (1, 'some_test.py'),
                        (1, 'some_sol.py'),
                        (1, 'population.csv'),
                        (1, 'jupman.py') ]    
    
def test_make_preamble_filelist_test_chapter_marked_chal():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/test-chapter/nb2-chal-sol.ipynb', True, '')  
    jcxt.jpre_dest_filepath = '_test/test-chapter/nb2-chal.ipynb'
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/test-chapter', lambda x : 'test-chapter')
    
    lst = jmt._make_preamble_filelist(jcxt, 
                                      f"{jcxt.jm.generated}/test-chapter.zip")

    assert lst == [(0, 'test-chapter'),                         
                        (1, 'extra'),                            
                            (2, 'nested'),
                                (3, 'other.csv'),
                                (3, 'something.txt'),                                
                            (2, 'whatever.pdf'),
                        (1, 'force-preprocess.ipynb'),
                        (1, 'nb.ipynb'),
                        (1, 'nb-sol.ipynb'),
                        (1, 'nb2-chal.ipynb', '*'),
                        (1, 'replacements.ipynb'),
                        (1, 'my_chal.py'),
                        (1, 'my_chal_test.py'),
                        (1, 'script.py'),
                        (1, 'some.py'),                        
                        (1, 'some_test.py'),
                        (1, 'some_sol.py'),
                        (1, 'population.csv'),
                        (1, 'jupman.py') ]      
    
def test_make_preamble_filelist_test_chapter_marked_nested():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/test-chapter/nb-sol.ipynb', True, '')  
    jcxt.jpre_dest_filepath = '_test/test-chapter/nb.ipynb'
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/test-chapter', lambda x : 'test-chapter')
    
    with pytest.raises(JupmanUnsupportedError):
        lst = jmt._make_preamble_filelist(jcxt, 
                                        f"{jcxt.jm.generated}/test-chapter.zip",                                      
                                        marked = ['extra/nested/something.txt'])
    
    
def test_make_preamble_filelist_test_chapter_no_ignored():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/test-chapter/nb-sol.ipynb', True, '')  
    jcxt.jpre_dest_filepath = '_test/test-chapter/nb.ipynb'
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/test-chapter', lambda x : 'test-chapter')
    
    lst = jmt._make_preamble_filelist(jcxt, 
                                      f"{jcxt.jm.generated}/test-chapter.zip",                                      
                                      ignored = [])
    
    assert lst == [(0, 'test-chapter'),    
                        (1, '_static'),
                            (2, 'img'),
                                (3, 'cc-by.png'),
                        (1, 'extra'),                            
                            (2, 'nested'),
                                (3, 'other.csv'),
                                (3, 'something.txt'),                                
                            (2, 'whatever.pdf'),
                        (1, 'img'),
                            (2, 'more'),
                                (3, 'pic2.png'),
                                (3, 'pic3.png'),
                            (2, 'pic1.png') ,                           
                        (1, 'force-preprocess.ipynb'),
                        (1, 'nb.ipynb', '*'),                        
                        (1, 'nb-sol.ipynb'),
                        (1, 'nb2-chal.ipynb'),
                        (1, 'replacements.ipynb'),
                        (1, 'my_chal.py'),
                        (1, 'my_chal_test.py'),
                        (1, 'script.py'),
                        (1, 'some.py'),                        
                        (1, 'some_test.py'),
                        (1, 'some_sol.py'),
                        (1, 'population.csv'),
                        (1, 'jupman.py')]
    
def test_make_preamble_filelist_test_chapter_no_marked_files():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/test-chapter/nb-sol.ipynb', True, '')    
    jcxt.jpre_dest_filepath = '_test/test-chapter/nb.ipynb'
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/test-chapter', lambda x : 'test-chapter')
    
    lst = jmt._make_preamble_filelist(jcxt, 
                                      f"{jcxt.jm.generated}/test-chapter.zip",                                      
                                      marked = [])    
       
    assert lst == [(0, 'test-chapter'),                         
                        (1, 'extra'),                            
                            (2, 'nested'),
                                (3, 'other.csv'),
                                (3, 'something.txt'),                                
                            (2, 'whatever.pdf'),
                        (1, 'force-preprocess.ipynb'),
                        (1, 'nb.ipynb'),                        
                        (1, 'nb-sol.ipynb'),
                        (1, 'nb2-chal.ipynb'),
                        (1, 'replacements.ipynb'),
                        (1, 'my_chal.py'),
                        (1, 'my_chal_test.py'),
                        (1, 'script.py'),
                        (1, 'some.py'),                        
                        (1, 'some_test.py'),
                        (1, 'some_sol.py'),
                        (1, 'population.csv'),
                        (1, 'jupman.py')]

def test_make_preamble_filelist_test_chapter_unspecified_marked_files():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/test-chapter/nb-sol.ipynb', True, '')    
    jcxt.jpre_dest_filepath = '_test/test-chapter/nb.ipynb'
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/test-chapter', lambda x : 'test-chapter')
    
    lst = jmt._make_preamble_filelist(jcxt, 
                                      f"{jcxt.jm.generated}/test-chapter.zip")
    
    assert lst == [(0, 'test-chapter'),                         
                        (1, 'extra'),                            
                            (2, 'nested'),
                                (3, 'other.csv'),
                                (3, 'something.txt'),                                
                            (2, 'whatever.pdf'),
                        (1, 'force-preprocess.ipynb'),
                        (1, 'nb.ipynb', '*'),
                        (1, 'nb-sol.ipynb'),
                        (1, 'nb2-chal.ipynb'),
                        (1, 'replacements.ipynb'),
                        (1, 'my_chal.py'),
                        (1, 'my_chal_test.py'),
                        (1, 'script.py'),
                        (1, 'some.py'),                        
                        (1, 'some_test.py'),
                        (1, 'some_sol.py'),
                        (1, 'population.csv'),
                        (1, 'jupman.py') ]


def test_make_preamble_filelist_test_chapter_non_existing_dest_file():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/test-chapter/nb666-sol.ipynb', True, '')    
    jcxt.jpre_dest_filepath = '_test/test-chapter/nb666.ipynb'    
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/test-chapter', lambda x : 'test-chapter')
    
    with pytest.raises(JupmanNotFoundError):
        lst = jmt._make_preamble_filelist(jcxt, 
                                          f"{jcxt.jm.generated}/test-chapter.zip")


def test_tutorial_preamble_ipynb():
    """ @since 3.6
    """
    jcxt = JupmanContext(make_sphinx_config(), '_test/test-chapter/nb-sol.ipynb', True, '')    
    jcxt.jpre_dest_filepath = '_test/test-chapter/nb.ipynb'
    jcxt.jm.repo_browse_url = 'https://github.com/DavidLeoni/jupman/blob/master/'
    jcxt.jm.chapter_files = ['jupman.py', '_static/img/cc-by.png']
    jmt.zip_folder(jcxt, '_test/test-chapter', lambda x : 'test-chapter')
    
    s = jcxt.jm.tutorial_preamble(jcxt)
    
    debug(s)
    #assert '' in s

