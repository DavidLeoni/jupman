import logging
# this way we don't get warning of other libs in pytest, see https://stackoverflow.com/a/63946841
logging.captureWarnings(True)  

import pprint
import collections.abc
from enum import Enum
import re
import os
import inspect
import types
import glob
import stat
import datetime 
import collections
import zipfile
import shutil
import itertools
from typing import List  # needed instead of list  with python < 3.9
from typing import Tuple # needed instead of tuple with python < 3.9
from typing import Iterable # in python < 3.9 this one is subscriptable, while collections.abc.Iterable is not.
    
import nbconvert
from typing import Union
import pathspec
from pylatexenc.latexencode import unicode_to_latex
from babel.dates import format_date
from subprocess import check_output
import nbsphinx
import nbformat


class JupmanFormatter(logging.Formatter):

    def format(self, record):
        if record.levelno == logging.INFO:
            self._style._fmt = "jupman: %(message)s"
        elif record.levelno in [logging.DEBUG, logging.WARNING, logging.CRITICAL]:
            self._style._fmt = "jupman %(levelname)-8s [%(filename)s:%(lineno)s]: %(message)s "        
        return super().format(record)


logger = logging.getLogger('jupman')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(JupmanFormatter())
logger.addHandler(console_handler)

# I know I shouldn't be doing this but apparently logging is so incredibly fucked up..
_log_level = os.environ.get('JUPMAN_LOG_LEVEL')
if _log_level:
    logging.getLogger().setLevel(_log_level)
    logger.debug('This is a debug message')
    logger.info(f'Setting logger level to {_log_level}')

def fatal(msg, ex=None):
    """ Prints error and exits (halts program execution immediatly)
    """
    if ex == None:
        exMsg = ""
    else:
        exMsg = " \n  %s" % repr(ex)
    logger.critical("\n\n    FATAL ERROR! %s%s\n\n" % (msg,exMsg))
    exit(1)

def error(msg, ex=None):
    """ Prints error and reraises exception (printing is useful as sphinx puts exception errors in a separate log)
    """
    if ex == None:
        exMsg = ""
        the_ex = Exception(msg)
    else:
        exMsg = " \n  %s" % repr(ex)
        the_ex = ex 
    logger.error("\n\n    FATAL ERROR! %s%s\n\n" % (msg,exMsg))
    raise the_ex
    
def info(msg=""):
    logger.info(msg)    

def warn(msg, ex=None):
    logger.warning(msg)    

   
debug = logger.debug


class _Mocker:
    
    def __init__(self, name):
        self.name = name
        
    def __getattr__(self, name):
        return _Mocker(self.name + '.' + name)
  
    def __str__(self):
        return self.name
  
    def __repr__(self):
        return self.name
  
  
""" Placeholder, ONLY to be used to prevent python from complaining about syntax / non-existing objects
@since 3.6
"""
_JUPMAN_ = _Mocker('_JUPMAN_')

""" Placeholder only to be used when there might be some ambiguity for the parser

i.e by writing  _JUPMAN_.a.b._END_.c.d it will substitute _JUPMAN_.a.b._END_ with _JUPMAN_.a.b

ONLY to be used to prevent python from complaining about syntax / non-existing objects
@since 3.6
"""
_END_ = _Mocker('_END_')
        

PREAMBLE_MARKED = ('CURRENT',)    
PREAMBLE_IGNORED = ('img/', '_static/')    


class JupmanError(Exception):
    pass

class JupmanNotFoundError(JupmanError):
    pass

class JupmanPreprocessorError(JupmanError):
    pass

class JupmanEmptyChapterError(JupmanPreprocessorError):
    pass


class JupmanUnsupportedError(JupmanError):
    pass

EXPR_PREFIX = '_JUPMAN_'
EXPR_PATTERN = re.compile(r'(_JUPMAN_(\.[a-zA-Z][\w]*)+((\((\w|,|\s)*\))|\._END_)?)')


def obj_to_repr(obj) -> str:
    return obj.__class__.__name__ + '(' +  ','.join([f"{k}={repr(v)}" for k,v in vars(obj).items()]) + ')'

def obj_to_str(obj) -> str:            
    return obj.__class__.__name__ + '(\n' +  pprint.pformat(vars(obj),  indent=4, width=1) + '\n)'


class Jupman:    
    """ 
        @deprecated in 3.6, use JupmanConfig instead
    """
    def __new__(cls):
        warn("Jupman class is DEPRECATED since 3.6, use JupmanConfig instead")
        return JupmanConfig()
    
    
class JupmanConfig:
    """ Holds Jupman-specific configuration for Sphinx build
    """

    def __init__(self):
        
        self.subtitle = "TODO CHANGE jm.subtitle"""
        self.course = "TODO CHANGE jm.course" 
        self.degree = "TODO CHANGE jm,degree"

        self.filename = 'jupman'   # The filename without the extension
        """ 'filename' IS *VERY* IMPORTANT !!!!
            IT IS PREPENDED IN MANY GENERATED FILES
            AND IT SHOULD ALSO BE THE SAME NAME ON READTHEDOCS 
            (like i.e. jupman.readthedocs.org) """

        self.chapter_files = ['jupman.py', 'my_lib.py', '_static/img/cc-by.png', 
                                
                            '_static/js/jupman.js',  # these files are injected when you call jupman.init()
                            '_static/css/jupman.css', 
                            '_static/js/toc.js',
                            
                            '_static/js/pytutor-embed.bundle.min.js.zip' ]
        """ Common files for exercise and exams as paths. Paths are intended relative to the project root. Globs like /**/* are allowed."""

        
        self.repo_browse_url = ''
        """ The repositoty url prefix for browsing files, i.e. 'https://github.com/DavidLeoni/jupman/blob/master/'
        """

        self.chapter_patterns =  ['*/']
        self.chapter_exclude_patterns =  ['[^_]*/','exams/', 'project/']

        self.ipynb_show_solution = "Show solution"
        self.ipynb_hide_solution = "Hide solution"
        self.ipynb_show_answer = "Show answer"
        self.ipynb_hide_answer = "Hide answer"

        self.ipynb_solutions = "SOLUTIONS"
        self.ipynb_exercises = "EXERCISES"
        """ words used in ipynb files - you might want to translate these in your language. Use plurals."""        

        self.write_solution_here = tag_regex("# write here", must_begin=False, preserve_line=True)
        """ the string is not just a translation, it's also a command that when 
        building the exercises removes the content after it in the code cell it is 
        contained in. """

        self.solution = tag_regex("# SOLUTION")
        """ #NOTE: the string is not just a translation, it's also a command
            that  when building the exercises completely removes the content of the cell 
            it is contained in (solution comment included)."""


        self.markdown_answer = tag_regex('**ANSWER**:')
        """NOTE: the string is not just a translation, it's also a command 
                 that  when building the exercises removes the content after it in
                 the markdown cell it is contained in.
        """

        self.zip_ignored = ['__pycache__', '**.ipynb_checkpoints', '.pyc', '.cache', '.pytest_cache', '.vscode',]
        """ Paths given here are intended relative to each zip own root, not project root.
        """

        self.formats = ["html", "epub", "latex"]


        self.build = "_build"
        # Output directory. Not versioned.
        
        self.generated='_static/generated'
        # Directory where to put zips. Versioned. 
        # NOTE: this is *outside* build directory

        self.manuals = {
            "student": {
                "name" : "Jupman",  # TODO put manual name, like "Scientific Programming"
                "audience" : "studenti",
                "args" : "",
                "output" : ""
            }
        }
        self.manual = 'student'

        self.raise_exc = "jupman-raise"
        self.strip = "jupman-strip"
        self.preprocess = "jupman-preprocess"
        self.purge = "jupman-purge"
        self.purge_io = "jupman-purge-io"
        self.purge_input = "jupman-purge-input"
        self.purge_output = "jupman-purge-output"
        
        

        self.raise_exc_code = "raise Exception('TODO IMPLEMENT ME !')"
        """ WARNING: this string can end end up in a .ipynb json, so it must be a valid JSON string  ! Be careful with the double quotes and \n  !!
        """


        self.solution_tags = [self.raise_exc, self.strip]
        """ Code cells containing these tags are considered solutions        
            @since 3.3
        """


        self.span_tags = [self.raise_exc, self.strip, self.purge]
        """ Tags which enclose a span of text
            @since 3.3
        """

        self.directive_tags = [self.preprocess, self.purge, self.purge_input, self.purge_output, self.purge_io]
        """ Code cells containing these tags are not considered a solution.
            @since 3.3
        """

        self.distrib_ext = ['py', 'ipynb']
        """ Supported distribution extensions
        """


        self.preprocessors = [JupmanPreprocessor(self)]
        """ Notebook preprocessors. Default one is JupmanPreprocessor.

            @since 3.2
        """
        
        self.html_index_links = """
<!-- HTML download links -->
<p>
 DOWNLOAD: &nbsp;&nbsp; <a href="https://jupman.softpython.org/en/latest/jupman.pdf" target="_blank">PDF</a>
           &nbsp;&nbsp; <a href="https://jupman.softpython.org/en/latest/jupman.epub" target="_blank"> EPUB </a>
           &nbsp;&nbsp; <a href="https://github.com/DavidLeoni/jupman/archive/gh-pages.zip" target="_blank"> HTML </a>
           &nbsp;&nbsp; <a href="https://github.com/DavidLeoni/jupman" target="_blank"> Github </a>
</p>           
<br/>
"""
        
        self.latex_index_fix_start = r"""
% Latex fixes, DO NOT DELETE THIS !!!!

% need to demote chapters to sections because sphinx promotes them *just in the home* :-/
% https://tex.stackexchange.com/questions/161259/macro-for-promoting-sections-to-chapters
% for alternatives, see https://texfaq.org/FAQ-patch

\let\truechapter\chapter
\let\truesection\section
\let\truesubsection\subsection
\let\truesubsubsection\subsubsection
\let\truethesection\thesection

\let\chapter\truesection
\let\section\truesubsection
% suspend number printing , according to   https://tex.stackexchange.com/a/80114
\renewcommand\thesection{}

\truesection{About}
"""

        self.latex_index_fix_overview = r"""
% Latex: fix for book structure

\let\thesection\truethesection
\truechapter{Overview}    
"""    
        
        self.latex_index_fix_end = r"""
% Latex: Restores all the previous substitutions 
% DO NOT DELETE THIS !!!!
 
\let\chapter\truechapter
\let\section\truesection
\let\subsection\truesubsection
\let\subsubsection\truesubsubsection        
"""        
        

    
    def tutorial_preamble(self,
                          jcxt,
                          marked: Iterable[str] = PREAMBLE_MARKED, 
                          ignored: Iterable[str] = PREAMBLE_IGNORED) -> str:
        """ 
            zip_name example:  prj-foldername.zip
            
            marked: list of files to show highlighted (files subfolders cannot be marked), first one is 
                    the one the user should open first special value 'CURRENT' represents current 
                    notebook destination (jcxt.jpre_dest_filepath)            
            ignored: ignored paths, supports glob
            
            TODO what about renamed zips like projects/project1/ -> prj-myproject1.zip  ?
            
            @since 3.6
        """        
        from pathlib import Path
        
        relpath = os.path.relpath(os.path.abspath(jcxt.jpre_dest_filepath))
        relfolder_name = Path(relpath).parts[-2]                
        
        debug(f'relpath: {relpath}')
        debug(f'relfolder_name: {relfolder_name}')
        debug(f'jcxt.jpre_dest_filepath: {jcxt.jpre_dest_filepath}')
        
        # should already exist during nbsphinx parsing
        zip_filepath = f"{jcxt.jm.generated}/{relfolder_name}.zip"        
         
        
        files = []
        for tup in _make_preamble_filelist(jcxt, zip_filepath, marked=marked, ignored=ignored):
            if len(tup) == 3:
                if tup[2] != '*':  # bold
                    raise JupmanPreprocessorError(f"Invalid marker symbol {tup[2]} found in tuple: {tup}")
                s = '    '*tup[0] + f"<strong>{tup[1]}</strong>"
            elif len(tup) == 2:
                s = '    '*tup[0] + tup[1]
            else:
                raise JupmanPreprocessorError(f"Invalid tuple length {len(tup)} for tuple: {tup}")
            files.append(s)
            
        files_str = '\n'.join(files)
        
        zip_web_rel_filepath = os.path.relpath(f"{jcxt.jm.generated}/{relfolder_name}.zip",
                                               os.path.abspath(jcxt.jpre_dest_filepath))
        
        browse_online_link = f"{jcxt.jm.repo_browse_url}{jcxt.jpre_dest_filepath}"
        
        return f"""

<a id="jupman-zip-download" href="{zip_web_rel_filepath}" target="_blank" title="Download exercises and solutions"> 
<img src="_static/img/jupman/download-zip.svg" alt="Download exercises and solutions">
</a>

<a id="jupman-zip-browse" href="{browse_online_link}" target="_blank" title="Browse files online"> 
<img src="_static/img/jupman/browse.svg" alt="Browse files online">
</a>

- unzip exercises in a folder, you should get something like this: 


<pre class="jupman-zip-list highlight">
{files_str}
</pre>


<div class="alert alert-warning">

**WARNING**: to correctly visualize the notebook, it MUST be in an unzipped folder !
</div>


- Run Jupyter application: a browser should open, showing a file list: navigate the list and open the notebook `TODO` (NOT the -sol, contains solutions!)
- Go on reading that notebook, some cells will invite you to write code into them. Shortcut keys:

    - to execute Python code inside a Jupyter cell, press `Control + Enter`
    - to execute Python code inside a Jupyter cell AND select next cell, press `Shift + Enter`
    - to execute Python code inside a Jupyter cell AND a create a new cell aftwerwards, press `Alt + Enter`
    
- If the notebooks looks stuck, try to select `Kernel -> Restart`
            
"""        
        
    def  __repr__(self):
        return obj_to_repr(self)

    def  __str__(self):
        return obj_to_str(self)

        
    def latex_maketitle(self, html_baseurl):
        """
            @deprecated since 3.6, use jupman_tools.latex_maketitle instead"
        """
        warn("DEPRECATED since 3.6, use jupman_tools.latex_maketitle instead")
        jcxt = JupmanContext.make_empty()
        jcxt.jm = self
        return latex_maketitle(jcxt, html_baseurl)
        
    def get_exercise_folders(self):
        """
            @deprecated since 3.6, use jupman_tools.get_exercise_folders instead"
        """
        warn("DEPRECATED since 3.6, use jupman_tools.get_exercise_folders instead")
        jcxt = JupmanContext.make_empty()
        jcxt.jm = self
        return get_exercise_folders(jcxt)

    def zip_folder(self, source_folder, renamer=None):
        """
            @deprecated since 3.6, use jupman_tools.zip_folder instead"
        """
        warn("DEPRECATED since 3.6, use jupman_tools.zip_folder instead")
        jcxt = JupmanContext.make_empty()
        jcxt.jm = self
        return zip_folder(jcxt, source_folder, renamer)        

    def zip_folders(self, selector, renamer=None):
        """
            @deprecated since 3.6, use jupman_tools.zip_folders instead"
        """
        warn("DEPRECATED since 3.6, use jupman_tools.zip_folders instead")
        jcxt = JupmanContext.make_empty()
        jcxt.jm = self
        return zip_folders(jcxt, selector, renamer)
        
    def zip_paths(self, rel_paths, zip_path, patterns=(), remap=None):
        """
            @deprecated since 3.6, use jupman_tools.zip_paths instead"
        """
        warn("DEPRECATED since 3.6, use jupman_tools.zip_paths instead")
        jcxt = JupmanContext.make_empty()
        jcxt.jm = self
        return zip_paths(jcxt, rel_paths, zip_path, patterns, remap)
        


class SphinxConfig:
    """ For now a place holder, in the future we may substitute with proper original sphinx config

        @deprecated
        @since 3.6 
    """
    def __init__(self, inp=None):
        """ Takes either a module or a dict-like object
        """
        raise Exception("DEPRECATED")
    
    def __getitem__(self, key):          
        return self.__dict__[key]
  
    def __setitem__(self, key, newvalue):    
        self.__dict__[key] = newvalue

    def  __repr__(self):
        return obj_to_repr(self)

    def  __str__(self):
        return obj_to_str(self)

    def __contains__(self, item):
        return item in self.__dict__
    
    
class JupmanContext:
    """ Context usable during preprocessor runs, merges sphinx config and adds 
        further variables prefixed with jpre_
    
        @since 3.6
    """    
      
    @staticmethod
    def make_empty():
        return JupmanContext({}, '', False) 
      
    def __init__(self, sphinx_config, source_filepath: str, website: bool):    
                
        self.jm = JupmanConfig()
              
        
        if not sphinx_config:
            pass
        elif isinstance(sphinx_config, collections.abc.Mapping):
            for k, v in sphinx_config.items():
                self.__dict__[k] = v
        elif sphinx_config == logging.__class__:  # class module
            for name, obj in inspect.getmembers(sphinx_config):
                self.__dict__[name] = obj
        elif hasattr(sphinx_config, '__dict__'):
            for k, v in sphinx_config.__dict__.items():
                self.__dict__[k] = v
        else:            
            raise ValueError(f'Unrecognized input type while creating {self.__class__.__name__}: {type(sphinx_config)}')
                
                
        self.jpre_source_filepath = source_filepath
        self.jpre_dest_filepath = source_filepath  # sometimes dest might differ from source, es generated exercises
        self.jpre_website = website
                
        
    def __repr__(self):
        """ @since 3.6
        """            
        return obj_to_repr(self)

    def  __str__(self):
        """ @since 3.6
        """            
        return obj_to_str(self)
        


def parse_date(ld):
    try:
        return datetime.datetime.strptime( str(ld), "%Y-%m-%d")
    except Exception as e:
        raise Exception("NEED FORMAT 'yyyy-mm-dd', GOT INSTEAD: '%s'" % ld, e)

    
def parse_date_str(ld) -> str:
    """
        NOTE: returns a string 
    """
    return str(parse_date(ld)).replace(' 00:00:00','')
    
def date_to_human(ld: Union[datetime.date, str], locale : str, formatter : str ='') -> str:
    """ Short human readable dates
    
        Default: something good for displaying exams in a toc, like   Wed 3, Apr 2007        
    """    
    
    if not formatter:
        fmt = "EEE d, MMM yyyy"
    else:
        fmt = formatter
    
    if isinstance(ld, str):
        d = parse_date(ld)
    else:
        d = ld
    
    intermediate = format_date(d, fmt, locale=locale)
    if fmt == "EEE d, MMM yyyy":
        # makes sure we get capital
        # who cares about silly grammar nuances https://stackoverflow.com/questions/18864957/capitalize-months-name-in-es-locale        
        return ', '.join([el.capitalize() for el in intermediate.split(', ')])
    else:
        return intermediate
    
    
def super_doc_dir():
    return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

def detect_release():
    """ Return a release string, calling git to find tags.
        If unsuccessful return 'dev'.
    """
    try:        
        release = check_output(['git', 'describe', '--tags', '--always'])
        release = release.decode().strip()        
        if not '.' in release:
            raise Exception                    
    except Exception:
        release = 'dev'

    return release

def get_version(release):
    """ Given x.y.z-something, return x.y
        On ill-formed return verbatim.
    """
    if '.' in release:
        sl = release.split(".")
        return  '%s.%s' % (sl[0], sl[1])
    else:
        return release


def expand_JM(source, target, exam_date, conf):
    """ @deprecated since 3.6
    """
    warn("expand_JM is deprecated! Please upgrade jupman to >= 3.6")
    
    d = parse_date(exam_date)
    sourcef = open(source, "r")
    s = sourcef.read()
    s = s.replace('_JM_{exam.date}', exam_date )
    s = s.replace('_JM_{exam.date_human}', d.strftime('%a %d, %b %Y') )
    for k in conf.__dict__:
        s = s.replace('_JM_{conf.' + k + '}', str(conf.__dict__[k]))
    for k in conf.jm.__dict__:
        s = s.replace('_JM_{conf.jm.' + k + '}', str(conf.jm.__dict__[k]))
    p = re.compile(r'_JM_\{[a-zA-Z][\w\.]*\}')
    if p.search(s):
        warn("FOUND _JM_ macros which couldn't be expanded!")
        warn("               file: %s" % source)
        warn("\n                 ".join(p.findall(s)))
        warn("")
    destf = open(target, 'w')    
    destf.write(s)





def _replace_title( nb_node, source_abs_fn, replacement, title_pat=r'(.*)') -> str:
        """ Finds the title of a notebook and replaces it with replacement
            Returns the old title.
        """
        
        # look for title

        pat = re.compile(r'^(\s*#\s+)'+ title_pat)
        for cell in nb_node.cells:
            if cell.cell_type == "markdown":
                ma = pat.search(cell.source)
                
                if ma:
                    found_title = ma.group(0)
                    cell.source = re.sub(pat, 
                                         replacement,
                                         cell.source) 
                    break
        
        if not ma:            
            error("Couldn't find title in file: \n   %s\nThere should be a markdown cell beginning with text # bla bla    Complete pattern: %s" % (source_abs_fn,pat.pattern)) 
        return found_title

class FileKinds(Enum):
    SOLUTION = 1
    EXERCISE = 2
    TEST = 3
    OTHER = 4
    CHALLENGE_SOLUTION = 5

    @staticmethod
    def prefix(fname, supp_ext):
        """ @since 3.6
        """
        for ext in supp_ext:
            if fname.endswith(f".{ext}"):
                sep = FileKinds.sep(ext)
                ft = FileKinds.detect(fname)
                if ft == FileKinds.SOLUTION:                    
                    return fname.rstrip(f"{sep}sol.{ext}")
                elif ft == FileKinds.CHALLENGE_SOLUTION:
                    return fname.rstrip(f"{sep}sol.{ext}")

    @staticmethod
    def sep(ext):
        if ext == 'py':
            return '_'
        else:
            return '-'
    
    @staticmethod
    def is_supported_ext(fname, supp_ext):
        for ext in supp_ext:
            if fname.endswith('.%s' % ext):
                return True
        return False
    
    @staticmethod
    def parse(fname : str):
        """ Returns a tuple like (type, prefix, file end, extension)
        
            Example 
            
            >>> FileKinds.parse('footbal-eurocup-chal-sol.ipynb')
            (FileKinds.CHALLENGE_SOLUTION, 'footbal-eurocup', '-chal-sol', 'ipynb')
            
            TODO EXERCISE / CHALLENGE are detected as OTHER
            https://github.com/DavidLeoni/jupman/issues/130
            
            @since 3.6
        """
        l = fname.split(".")
        if len(l) > 0:
            ext = l[-1]
        else:
            ext = ''
        sp = FileKinds.sep(ext)
        chal_sol_end  = f'{sp}chal{sp}sol.{ext}'
        chal_end  = f'{sp}chal.{ext}'
        sol_end = f'{sp}sol.{ext}'
        test_end = "_test.py"
        if fname.endswith(chal_sol_end):
            return (FileKinds.CHALLENGE_SOLUTION, fname.split(chal_sol_end)[0], chal_sol_end[:-len(f'.{ext}')], ext)
        if fname.endswith(chal_end):
            #TODO could be exercise ??
            return (FileKinds.OTHER, fname.split(chal_end)[0], chal_end[:-len(f'.{ext}')], ext)
        elif fname.endswith(sol_end):
            return (FileKinds.SOLUTION, fname.split(sol_end)[0], sol_end[:-len(f'.{ext}')], ext)
        elif fname.endswith(test_end) :            
            return (FileKinds.TEST, fname.split(test_end)[0], test_end[:-len(f'.{ext}')], ext)
        else:            
            return (FileKinds.OTHER, fname.split(f'.{ext}')[0], '', ext)
    
    
    @staticmethod
    def detect(fname : str):
        return FileKinds.parse(fname)[0]

    @staticmethod
    def check_ext(fname, supp_ext):
        if not FileKinds.is_supported_ext(fname, supp_ext):
            raise Exception("%s extension is not supported. Valid values are: %s" % (fname, supp_ext))
        
    @staticmethod        
    def exercise(radix, ext, supp_ext):      
        FileKinds.check_ext(ext,supp_ext)
        return radix + "." + ext

    @staticmethod
    def exercise_from_solution(fname, supp_ext):
        FileKinds.check_ext(fname, supp_ext)
        ext = fname.split(".")[-1]
               
        return fname.replace(FileKinds.sep(ext) + "sol." + ext, "." + ext)
        
    @staticmethod
    def solution(radix, ext, supp_ext):
        FileKinds.check_ext(ext, supp_ext)
        return radix + FileKinds.sep(ext) + 'sol.' + ext

    @staticmethod
    def test(radix):
        return radix + '_test.py'

    
    

def check_paths(path, path_check):
    if not isinstance(path, str):
        raise ValueError("Path to delete must be a string! Found instead: %s " % type(path))
    if len(path.strip()) == 0:
        raise ValueError("Provided an empty path !")
    if not isinstance(path_check, str):
        raise ValueError("Path check to delete must be a string! Found instead: %s" % type(path_check))
    if len(path_check.strip()) == 0:
        raise ValueError("Provided an empty path check!")
    if not path.startswith(path_check):        
        fatal("FAILED SAFETY CHECK FOR DELETING DIRECTORY %s ! \n REASON: PATH DOES NOT BEGIN WITH %s" % (path, path_check) )

def uproot(path):
    """ Returns a relative path from input path to root.
        
        NOTE: IT IS SUPPOSED TO BE RUN FROM A PYTHON FILE RESIDING *AT ROOT LEVEL*

        Example:
        >>> uproot('_static/img/cc-by.png')
        >>>  '../../'
        >>> uproot('_static')
        >>>  '../'
        
        TODO: review behaviour an non-existing paths, seems inconsistent.
    """
    if not path:
        raise ValueError('Invalid filepath=%s' % path)

    ret = os.path.relpath(os.path.abspath(os.getcwd()),
                          os.path.abspath(path))
    if os.path.isfile(path) and ret.endswith('..'):
        ret = ret[:-2]
    if ret.endswith('..'):
        ret = f"{ret}/"
    return ret


def delete_tree(path, path_check):
    """ Deletes a directory, checking you are deleting what you really want

        path: the path to delete as a string
        path_check: the beginning of the path to delete, as a string
    """
    info("Cleaning %s  ..." % path)
    check_paths(path, path_check)

    if not os.path.isdir(path):
        raise Exception("Provided path is not a directory: %s" % path)

    #duplicated check (it's already in check_paths, but just to be sure)
    if path.startswith(path_check):
        shutil.rmtree(path)
    else:
        fatal("FAILED SAFETY CHECK FOR DELETING DIRECTORY %s ! \n REASON: PATH DOES NOT START WITH %s" % (path, path_check) )


def delete_file(path, path_check):
    """ Deletes a file, checking you are deleting what you really want

        path: the path to delete as a string
        path_check: the beginning of the path to delete, as a string
    """
    info("Cleaning %s  ..." % path)
    check_paths(path, path_check)

    if not os.path.isfile(path):
        raise Exception("Provided path is not a file: %s" % path)

    #duplicated check (it's already in check_paths, but just to be sure)
    if path.startswith(path_check):
        os.remove(path)
    else:
        fatal("FAILED SAFETY CHECK FOR DELETING FILE %s ! \n REASON: PATH DOES NOT START WITH %s" % (path, path_check) )


def tag_start(tag):
    return '#' + tag

def tag_end(tag):
    return '#/' + tag

def tag_regex(string, must_begin=True, preserve_line=False):
    """ Takes a non-regex string and return a regex string which ignores extra
        spaces in s and newline after 

        must_begin : if True, provided string must be at the beginning of code / cell
        preserve_line : if True, characters following the tag until the end of the line are ignored

        @since 3.3
    """
    if len(string) == 0:
            raise ValueError("Expect a non-empty string !")
    # so we do not get spaces escaped, which I find horrible default behaviour: 
    # https://stackoverflow.com/questions/32419837/why-re-escape-escapes-space
    escaped = [re.escape(x) for x in string.split()] 
    removed_spaces = r'\s+'.join(escaped)
    begin_char= r'^' if must_begin else ''
    if preserve_line:
        preservel = r'(.*?)\n'
    else:
        preservel = r'()'
    return r"(?s)(%s\s*%s)%s(.*)" % (begin_char, removed_spaces, preservel)

def ignore_spaces(string, must_begin=True):
    """ Takes a non-regex string and return a regex string which ignores extra
        spaces in s and newline after 

        must_begin : if True, provided string must be at the beginning of code / cell
        
        @deprecated: use tag_regex instead
    """
    warn("DEPRECATED: jupman_tools.ignore_spaces is deprecated, use tag_regex instead")
    return tag_regex(string, must_begin)

def multi_replace(text, d):
    """ Takes a dictionary pattern -> substitution and applies all substitutions to text
    """
    s = text
    for key in d:
        s = re.sub(key, d[key], s) 
    return s

def span_pattern(tag):
    """ NOTE: Doesn't eat the blank afterwards, has lookahead
    
        @since 3.3
    """
    s = r"%s(.*?)%s" % (start_tag_pattern(tag).pattern, end_tag_pattern(tag).pattern)
    
    return re.compile(s, flags=re.DOTALL)

def start_tag_pattern(tag):
    """ NOTE: start tag always eats the blank afterwards, end tag doesn't (has lookahead)
    
        @since 3.3
    """    
    return re.compile(r"#%s\s" % tag, flags=re.DOTALL)

def end_tag_pattern(tag):
    """ NOTE: start tag always eats the blank afterwards, end tag doesn't (has lookahead)
    
        @since 3.3
    """
    ec = tag_end(tag)[-1]
    s = r"%s((%s$)|(%s(?=\s)))" % (tag_end(tag)[:-1], ec, ec)
    return re.compile(s, flags=re.DOTALL)

def single_tag_pattern(tag):
    """ NOTE: Doesn't eat the blank afterwards, has lookahead
        @since 3.3
    """
    
    ec = tag_start(tag)[-1]
    s = r"%s((%s$)|(%s(?=\s)))" % (tag_start(tag)[:-1], ec, ec)
    return re.compile(s, flags=re.DOTALL)


def init(jm, sphinx_config=None) -> JupmanContext:
    """Initializes the system, does patching, etc

        Should be called in conf.py at the beginning of setup() 
    
        @since 3.2
    """
            
    
    if not sphinx_config:
        raise ValueError("globals() not passed to jmt.init call, please add it!")        
    
    #TODO a check would be nice but I'm lazy
    #if not sphinx_config.jm:
    #    raise ValueError("jm variable not present in sphinx config, please define it!")    
    

    if os.environ.get('GOOGLE_ANALYTICS'):
        info("Found GOOGLE_ANALYTICS environment variable")                
        sphinx_config.html_theme_options['analytics_id'] = os.environ.get('GOOGLE_ANALYTICS')
    else:
        info('No GOOGLE_ANALYTICS environment variable was found, skipping it')
    

    jcxt = JupmanContext(sphinx_config, '', False)
    
    info("release: %s" % jcxt.release)
    
    # hooks into ExecutePreprocessor.preprocess to execute our own filters.
    # Method as in https://github.com/spatialaudio/nbsphinx/issues/305#issuecomment-506748814

    def _from_notebook_node(self, nb, resources, **kwargs):
        debug('patched nbsphinx from_notebook_node')
                                
        for p in jcxt.jm.preprocessors:
            p.jcxt = jcxt             
            nb, resources = p.preprocess(nb, resources=resources)

        return nbsphinx_from_notebook_node(self, nb, resources=resources, **kwargs)        
        
    nbsphinx_from_notebook_node = nbsphinx.Exporter.from_notebook_node                
    
    nbsphinx.Exporter.from_notebook_node = _from_notebook_node
    
    return jcxt

def make_stripped_cell_id(cid):
    """ Given a solution id, creates a predictable new one 
            
        @since 3.3
    """
    
    #See https://nbformat.readthedocs.io/en/latest/format_description.html#cell-ids
    
    mx = 64    
    postfix = "-stripped"  # note: - is legal
        
    cand = cid + postfix
    if len(cand) > mx:
        return cid[:len(cid)-len(postfix)] + postfix
    else:
        return cand


class JupmanPreprocessor(nbconvert.preprocessors.Preprocessor):
    """ @since 3.2 """


    def __init__(self, jcxt : JupmanContext):
        """ @since 3.2 """
        super().__init__()
        self.jcxt = jcxt
        
    
    def preprocess(self, nb, resources):
        """ @since 3.2 """        
        
        """Careful path *includes* part of docname:
        resources:
        {   
            'metadata': {
                            'path': '/home/da/Da/prj/jupman/prj/jupyter-example'
                        },
            'nbsphinx_docname': 'jupyter-example/jupyter-example-sol',
            'nbsphinx_save_notebook': '/home/da/Da/prj/jupman/prj/_build/html/.doctrees/nbsphinx/jupyter-example/jupyter-example-sol.ipynb',
            'output_files_dir': '../_build/html/.doctrees/nbsphinx',
            'unique_key': 'jupyter-example_jupyter-example-sol'
        }
        """
        rel_dir, partial_fn = os.path.split(resources['nbsphinx_docname'])                
        source_abs_fn = os.path.join(resources['metadata']['path'], partial_fn + '.ipynb')     
        
        #TODO don't know if copy is strictly necessary, thinking about multithreading            
        njcxt = JupmanContext(self.jcxt, source_abs_fn, True)        
        
        if _is_to_preprocess(njcxt, nb):
            relpath = os.path.relpath(source_abs_fn, os.path.abspath(os.getcwd()))
            info("JupmanPreprocessor: parsing %s" % relpath )            
            
            try:
                validate_tags(njcxt, source_abs_fn)
            except Exception as ex:
                logger.warning("Failed Jupman tags validation! %s", ex)
                                   
            _sol_nb_to_ex(njcxt, nb)
            return nb, resources
        else:
            return nb, resources


def replace_py_rel(code : str, filepath : str) -> str:
    """ Takes code to be copied into zips and returns string without unneeded relative imports
    """
    upr = uproot(filepath).replace('.',r'\.')     
    if len(re.findall(r'sys\..+', code)) > 1:
        repl = r'import sys\n'
    else:
        repl = ''
    
    ret =  re.sub(r'import\s+sys\s*;?\s*\nsys\.path.append\([\'\"]((%s))[\'\"]\)\s*;?\s*' % upr,   
                repl,
                code)
    return ret

def replace_md_rel(code : str, filepath : str) -> str: 
    """ Takes markdown to be copied into zips and returns string with relative paths removed
    """
    upr = uproot(filepath).replace('.',r'\.')     
    
    ret =  re.sub(r'(\[.*?\]\()(%s)(.*?\))' % upr,               
                  r"\1\3",
                  code)
    
    ret = replace_html_rel(ret, filepath)
    return ret


def replace_html_rel(code : str, filepath : str) -> str:
    
    """ Takes html to be copied into zips and returns string with relative paths removed
    
        NOTE: supported syntax is very rigid!    
    """    
    upr = uproot(filepath).replace('.',r'\.')

    ret =  re.sub(r'(<a\s+)(target=\"_blank\"\s+)*(href=\")(%s)(.*?\"(\s+.*?=\".*?\")*>)' % upr,               
                  r"\1\2\3\5",
                  code)

    ret =  re.sub(r'(<img\s+)(alt=\".*\"\s+)*(src=\")(%s)(.*?\"(\s+.*?=\".*?\")*>)' % upr,
                  r"\1\2\3\5",
                  ret)        
    
    ret =  re.sub(r'(<script\s+src=\")(%s)(.+?.js\")' % upr,
                  r"\1\3",
                  ret) 
    
    ret =  re.sub(r'(<style>[\s\n]*\@import[\s\n]+"?)(%s)(.+.css"?)' % upr,
                  r"\1\3",
                  ret)         
        
    return ret




def replace_ipynb_rel(nb_node, filepath : str, website : bool = False) -> str:
    """ MODIFIES nb_node without returning it !
    """
    
    for cell in nb_node.cells:
            
        if cell.cell_type == "code":    
            cell.source = replace_py_rel(cell.source, filepath)
            if not website:
                for output in cell.outputs:                    
                    if 'data' in output:
                        if "text/html" in output.data:
                            output.data["text/html"] = replace_html_rel(output["data"]["text/html"], filepath)


        elif cell.cell_type == "markdown":
            # markdown cells: fix rel urls
            if not website:
                cell.source = replace_md_rel(cell.source, filepath)                
        elif cell.cell_type == "raw" and \
                'raw_mimetype' in cell.metadata and cell.metadata['raw_mimetype'] == 'text/html':
            if not website:
                cell.source = replace_html_rel(cell.source, filepath)             
        else:
            #TODO rst, latex ?
            """ 
            "cell_type": "raw",
            "metadata": {
                "raw_mimetype": "text/restructuredtext"
            },
            
                "cell_type": "raw",
            "metadata": {
                "raw_mimetype": "text/latex"
            },
            """                                


        

def replace_templates(jcxt : JupmanContext, text : str) -> str:
    """ Takes text to be copied into zips and returns string with _JUPMAN_ templates replaced with fields from config
    
        @since 3.6
    """
                    
    
    problems = []    
    
    def f(m):
        try:
            obj = jcxt
            fields = m.group(0).split('.')
            
            
            for field in fields[1:]:
                pfield = field[:-2] if field.endswith('()') else field                
                
                if pfield == '_END_':
                    break
                
                if not hasattr(obj, pfield):                    
                    raise JupmanPreprocessorError(f"Attribute {pfield} not found in expression", m.group(0))
                                                
                if type(obj) in [logging.__class__]:                    
                    raise JupmanPreprocessorError(f"Found an unsupported attribute {pfield} of type {type(obj)} in expression", 
                                    m.group(0))
                
                try:
                    obj = getattr(obj, pfield)
                except Exception as ex:
                    raise JupmanPreprocessorError(f"Couldn't get attribute {pfield} from type {type(obj)} in expression. Reason: {str(ex)}", m.group(0))                                

                #TODO check function signature
                #def foo(a, b, c=4, *arglist, **keywords): pass
                #import inspect
                #inspect.getfullargspec(foo)
                #FullArgSpec(args=['a', 'b', 'c'], varargs='arglist', varkw='keywords', defaults=(4,), kwonlyargs=[], kwonlydefaults=None, annotations={})
                if field.endswith('()'):
                    try:
                        obj = obj(jcxt)
                    except Exception as ex:
                        raise JupmanPreprocessorError(f"Couldn't execute function {pfield} in expression. Reason: {str(ex)}", m.group(0))                                 
                elif '(' in field: #TODO handle blanks
                    raise JupmanPreprocessorError(f"To call a function you must put exactly () at the end with no spaces, function calling with parameters is not supported yet")
                    
            if isinstance(obj, str):
                return obj
            else:
                return pprint.pformat(obj)
            
        except Exception as ex:            
            problems.append(ex)
            return m.group(0)
        
    ret = re.sub(EXPR_PATTERN, f, text)        
        
    if len(problems) > 0:
        warn("Found _JUPMAN_ templates which couldn't be expanded!")
        warn("               file: %s" % jcxt.jpre_source_filepath)            
        warn("\n                 ".join([str(p) for p in problems]))
        warn("")                
        
    return ret


def replace_ipynb_templates(jcxt : JupmanContext, nb_node):
    """ MODIFIES nb_node without returning it !
    
        @since 3.6
    """    
    
   
    debug(f"Replacing templates in {jcxt.jpre_dest_filepath}")    

    for cell in nb_node.cells:
            
        if (cell.cell_type in ["code", "markdown"]) \
           or (cell.cell_type == "raw"  and 'raw_mimetype' in cell.metadata \
               and cell.metadata['raw_mimetype'] in ['text/html', 'text/restructuredtext', 'text/latex']):               
           
           cell.source = replace_templates(jcxt, cell.source)
        

def _purge_tags(jcxt : JupmanConfig, text : str) -> str:
    """ Purges text according to directives, and removes all other Jupman tags. Only the tags, not their content!
        
        WARNING: in other words, this function IS *NOT* SUFFICIENT 
                to completely clean exercises from solutions !!!
        
        @since 3.3
    """
    ret = text
    if jcxt.jm.purge_input in text or jcxt.jm.purge_io in text:  
        return ''
    #NOTE: span_pattern doesn't eat the blank afterwards (has lookahead)
    ret = re.sub(span_pattern(jcxt.jm.purge), '', ret)
                
    # so longer come first
    all_tags = sorted(set(jcxt.jm.solution_tags + jcxt.jm.directive_tags), reverse=True)
        
    
    for tag in all_tags:
        if tag in jcxt.jm.span_tags:
            #NOTE: start tag always eats the blank afterwards, end tag doesn't (has lookahead)
            ret = re.sub(start_tag_pattern(tag), '\n', ret)                
            ret = re.sub(end_tag_pattern(tag), '', ret)
            
        else:
            #NOTE: single_tag_pattern doesn't eat the blank afterwards (has lookahead)
            ret = re.sub(single_tag_pattern(tag), '', ret)            
    
    return ret


def is_zip_ignored(jcxt : JupmanContext, fname):    
    spec = pathspec.PathSpec.from_lines('gitwildmatch', jcxt.jm.zip_ignored)
    return spec.match_file(fname)
            

def get_exercise_folders(jcxt : JupmanContext):
    ret = []
    for p in jcxt.jm.chapter_patterns:
        for r in glob.glob(p):
            if r not in ret:
                ret.append(r)
    for p in jcxt.jm.chapter_exclude_patterns:
        for r in glob.glob(p):
            if r in ret:
                ret.remove(r)
    return ret


def is_code_sol(jcxt : JupmanContext, solution_text):
    """ Returns True if a cell contains any elements to be stripped in a solution           
    """
    njcxt = JupmanContext(jcxt, '', jcxt.jpre_website)    
    return sol_to_ex_code(njcxt, solution_text, parse_directives=False).strip() != solution_text.strip()


def is_to_strip(jcxt : JupmanContext, solution_text):
    """ Returns True if a cell contains any elements to strip

        @since 3.3
    """
    njcxt = JupmanContext(jcxt, '', jcxt.jpre_website)    
    return sol_to_ex_code(njcxt, solution_text, parse_directives=True).strip() != solution_text.strip()
    

def sol_to_ex_code(jcxt : JupmanContext, solution_text, parse_directives=True):
    
    ret = solution_text
    
    if parse_directives:            
        if jcxt.jm.purge_input in solution_text or jcxt.jm.purge_io in solution_text:
            return ''
        ret = replace_templates(jcxt, ret)
        ret = re.sub(span_pattern(jcxt.jm.purge), '', ret)
        for tag in sorted(jcxt.jm.directive_tags, reverse=True):
            ret = re.sub(single_tag_pattern(tag), '', ret)                                                                                        

    if re.match(jcxt.jm.solution, ret.strip()):
        return ''

    ret = re.sub(span_pattern(jcxt.jm.raise_exc), 
                 jcxt.jm.raise_exc_code, 
                 ret)
    
    ret = re.sub(span_pattern(jcxt.jm.strip), '', ret)
                
    ret = re.sub(jcxt.jm.write_solution_here, r'\1\2\n\n', ret)
    
    if jcxt.jpre_source_filepath:
        ret = replace_py_rel(ret, jcxt.jpre_source_filepath)
        
    return ret            

def validate_tags(jcxt : JupmanContext, fname : str) -> int:
    """ Validates jupman tags in file fname and return the number of solution tags found.
    """
    ret = 0
    if fname.endswith('.ipynb'):
        
        nb_node = nbformat.read(fname, nbformat.NO_CONVERT)        
        for cell in nb_node.cells:            
            if cell.cell_type == "code":    
                ret += validate_code_tags(jcxt, cell.source, fname)
            elif cell.cell_type == "markdown":
                ret += validate_markdown_tags(jcxt, cell.source, fname)                

    elif fname.endswith('.py'):
        with open(fname) as f:
            ret += validate_code_tags(jcxt, f.read(), f)
    else:
        raise ValueError('File format not supported for %s' % fname)
    return ret

def validate_code_tags(jcxt : JupmanContext, text : str, fname : str) -> int:
    """ Validates text which was read from file fname:

        - raises ValueError on mismatched tags
        - returns the number of solution tags found
    """
            
    tag_starts = {}
    tag_ends = {}
    ret = 0

    for tag in jcxt.jm.span_tags:
        tag_starts[tag] = len(re.compile(tag_start(tag) + r'\s').findall(text))
        tag_ends[tag] = len(re.compile(end_tag_pattern(tag)).findall(text))
        
        if tag in jcxt.jm.solution_tags:
            ret += tag_starts[tag]

    for tag in tag_starts:
        if tag not in tag_ends or tag_starts[tag] != tag_ends[tag] :
            raise ValueError("Missing final tag %s in %s" % (tag_end(tag), fname) )

    for tag in tag_ends:
        if tag not in tag_starts or tag_starts[tag] != tag_ends[tag] :
            raise ValueError("Missing initial tag %s in %s" % (tag_start(tag), fname) )
    
    ret += len(re.compile(jcxt.jm.write_solution_here).findall(text))
    ret += len(re.compile(jcxt.jm.solution).findall(text))
    
    return ret

def validate_markdown_tags(jcxt : JupmanContext, text : str, fname : str) -> int:
    return len(re.compile(jcxt.jm.markdown_answer).findall(text))


#TODO source_fn may be redundant
def _copy_test(jcxt : JupmanContext,  source_fn : str, dest_fn : str):
    
    source_abs_fn = jcxt.jpre_source_filepath
    
    with open(source_abs_fn, encoding='utf-8') as source_f:        
        
        data = source_f.read()
        data = replace_templates(jcxt, data)
        data= multi_replace(data, {
            r'from\s+(.+)_sol\s+import\s+(.*)' : r'from \1 import \2',
            r'import\s+(.+)_sol((\s*)|,)':r'import \1\2', 
            
        })
        data = replace_py_rel(data, source_abs_fn)
        
        info('  Writing (patched) %s' % dest_fn) 
        with open(dest_fn, 'w', encoding='utf-8') as dest_f:
            dest_f.write(data)        

#TODO source_fn may be redundant
def _copy_other(jcxt : JupmanContext, source_fn : str, dest_fn : str, new_root : str = ''):
    
    source_abs_fn = jcxt.jpre_source_filepath
    
    if source_abs_fn.endswith('.py') :
        with open(source_abs_fn, encoding='utf-8') as source_f:
            data = source_f.read()
            data = replace_templates(jcxt, data)
            data = replace_py_rel(data, source_abs_fn)
            info('  Writing (patched) %s' % dest_fn) 
        with open(dest_fn, 'w', encoding='utf-8') as dest_f:
            dest_f.write(data)
    elif source_abs_fn.endswith('.md') :
        with open(source_abs_fn, encoding='utf-8') as source_f:
            data = source_f.read()
            data = replace_templates(jcxt, data)
            data = replace_md_rel(data, source_abs_fn)
            info('  Writing (patched) %s' % dest_fn) 
        with open(dest_fn, 'w', encoding='utf-8') as dest_f:
            dest_f.write(data)
    elif source_abs_fn.endswith('.html') :
        with open(source_abs_fn, encoding='utf-8') as source_f:
            data = source_f.read()
            data = replace_templates(jcxt, data)
            data = replace_html_rel(data, source_abs_fn)
            info('  Writing (patched) %s' % dest_fn) 
        with open(dest_fn, 'w', encoding='utf-8') as dest_f:
            dest_f.write(data)
    elif source_abs_fn.endswith('.ipynb') :
        
        # note: for weird reasons nbformat does not like the sol_source_f 
        nb_node = nbformat.read(source_abs_fn, nbformat.NO_CONVERT)
        replace_ipynb_templates(jcxt, nb_node)
        replace_ipynb_rel(nb_node, source_abs_fn)
        info('  Writing (patched) %s' % dest_fn) 
        nbformat.write(nb_node, dest_fn)
    else:
        info("  Writing %s " % dest_fn)
        shutil.copy(source_abs_fn, dest_fn)        
                
#TODO source_fn may be redundant                
def _copy_sols(jcxt : JupmanContext, source_fn : str, dest_fn : str):
    
    source_abs_fn = jcxt.jpre_source_filepath
        
    if source_fn.endswith('.py'):
        
        with open(source_abs_fn) as sol_source_f:
            text = sol_source_f.read()
            found_total_purge = jcxt.jm.purge_input in text or jcxt.jm.purge_output in text or jcxt.jm.purge_io in text or ''
            if found_total_purge:
                raise ValueError("Found %s in python file %s, but it is only allowed in notebooks!" % (found_total_purge, source_fn))
            
            text = replace_templates(jcxt, text)
            text = replace_py_rel(text, source_abs_fn)                
            text = _purge_tags(jcxt, text)
            with open(dest_fn, 'w') as solution_dest_f:
                info("  Writing (patched) %s " % dest_fn)
                solution_dest_f.write(text)
    elif source_fn.endswith('.ipynb'):
        # py cells: strip jupman tags, fix rel urls
        
        # note: for weird reasons nbformat does not like the sol_source_f 
        nb_node = nbformat.read(source_abs_fn, nbformat.NO_CONVERT)
        replace_ipynb_templates(jcxt, nb_node)
        replace_ipynb_rel(nb_node, source_abs_fn)
        for cell in nb_node.cells:            
            if cell.cell_type == "code":                                            
                if jcxt.jm.purge_output in cell.source or jcxt.jm.purge_io in cell.source:
                    cell.outputs = []                        
                if (jcxt.jm.purge_input in cell.source and jcxt.jm.purge_output in cell.source) \
                    or jcxt.jm.purge_io in cell.source:
                    cell.metadata['nbsphinx'] = 'hidden'
                    
                cell.source = _purge_tags(jcxt, cell.source)

        nbformat.write(nb_node, dest_fn)
        
    else: # solution format not supported                           
        info("Writing %s" % source_fn)
        shutil.copy(source_abs_fn, dest_fn)
        

def _sol_nb_to_ex(jcxt : JupmanContext, nb):
    """ Takes a solution notebook object and modifies it to strip solutions  
        
        @since 3.2
    """    
    from nbformat.v4 import new_raw_cell

    def before_cell(n, cell_type):            
        
        if cell_type == 'code': 
            show = jcxt.jm.ipynb_show_solution
            hide = jcxt.jm.ipynb_hide_solution
            sol_class = 'jupman-sol-code'
        elif cell_type == 'markdown':
            show = jcxt.jm.ipynb_show_answer
            hide = jcxt.jm.ipynb_hide_answer
            sol_class = 'jupman-sol-question'
        else:
            warn("NO LABEL FOUND FOR cell_type %s, using default ones!" % cell_type)
            show = jcxt.jm.ipynb_show_solution
            hide = jcxt.jm.ipynb_hide_solution
            sol_class = 'jupman-sol-code'

        
        s = """<a  class="jupman-sol jupman-sol-toggler" """
        s += """\n onclick="jupman.toggleSolution(this);" """
        s += """\n data-jupman-show="%s" data-jupman-hide="%s">%s</a>""" % (show, hide, show)
        s += """<div class="jupman-sol %s" style="display:none">  """ % sol_class
        
        ret = new_raw_cell()
        ret.metadata.format = "text/html"
        ret.source = s
        return ret
        

    def after_cell():
        ret = new_raw_cell()
        ret.metadata.format = "text/html"
        ret.source = """</div>"""
        return ret            


    import copy
    
    source_abs_fn = os.path.abspath(jcxt.jpre_source_filepath)
            
    replace_ipynb_templates(jcxt, nb)
    replace_ipynb_rel(nb, source_abs_fn, jcxt.jpre_website)    
    
    
    if not jcxt.jpre_website:            
        if FileKinds.detect(source_abs_fn) == FileKinds.CHALLENGE_SOLUTION:
            _replace_title(nb, 
                            source_abs_fn, 
                            r"# \2", 
                            title_pat=r'(.*?)\s+(%s)' % jcxt.jm.ipynb_solutions)
        else:
            _replace_title(nb, 
                        source_abs_fn, 
                        r"# \2 %s" % jcxt.jm.ipynb_exercises)
    
    # look for tags
    sh_cells = nb.cells[:]
    nb.cells = []      

    cell_counter = 0

    for cell in sh_cells:
        stripped_cell = copy.deepcopy(cell)
        if "id" in cell:
            stripped_cell["id"] = make_stripped_cell_id(cell["id"])

        if cell.cell_type == "code":
            if is_to_strip(jcxt, cell.source):
                                                        
                if jcxt.jm.purge_output in cell.source or jcxt.jm.purge_io in cell.source:
                    stripped_cell.outputs = []
                    
                if (jcxt.jm.purge_input in cell.source and jcxt.jm.purge_output in cell.source) \
                    or jcxt.jm.purge_io in cell.source:
                    stripped_cell.metadata['nbsphinx'] = 'hidden'
                    
                
                
                stripped_cell.source = sol_to_ex_code(jcxt, cell.source)
                if jcxt.jpre_website:
                    
                    
                    if jcxt.jm.purge_input in cell.source or jcxt.jm.purge_io in cell.source:
                        #weird stuff: https://github.com/jupyter/nbconvert/blob/42cfece9ed07232c3c440ad0768b6a76f667fe47/nbconvert/preprocessors/tagremove.py#L98
                        #NOTE: this MUST be ONLY for website as transient is not even an nbformat valid field !
                        if getattr(stripped_cell, 'transient', None):
                            stripped_cell.transient['remove_source'] = True
                        else:
                            stripped_cell.transient = {
                                'remove_source': True
                            }
                    
                    if is_code_sol(jcxt, cell.source) \
                        and not (jcxt.jm.purge_input in cell.source or jcxt.jm.purge_io in cell.source):
                        nb.cells.append(before_cell(cell_counter, cell.cell_type))
                                                    
                        cell.source = _purge_tags(jcxt, cell.source)
                        nb.cells.append(cell)
                        nb.cells.append(after_cell())
                nb.cells.append(stripped_cell)
            else:
                nb.cells.append(cell)
        elif cell.cell_type == "markdown":                    
            if re.match(jcxt.jm.markdown_answer, cell.source.strip()):
                if jcxt.jpre_website:
                    nb.cells.append(before_cell(cell_counter, cell.cell_type))
                    nb.cells.append(cell)
                    nb.cells.append(after_cell()) 
                else:
                        # substitutes with newline, otherwise it shows 'Type markdown or latex'   
                    stripped_cell.source = re.sub( jcxt.jm.markdown_answer, 
                                                   r"\1\n",  
                                                   cell.source.strip())
                    
                    nb.cells.append(stripped_cell)                   
            else:
                nb.cells.append(cell)
        else:
            nb.cells.append(cell)

        cell_counter += 1
                    


def _is_to_preprocess(jcxt : JupmanContext, nb):
    """
        @since 3.3
    """
    source_abs_fn = jcxt.jpre_source_filepath
    
    if source_abs_fn.endswith('.ipynb'):
        
        fileKind = FileKinds.detect(source_abs_fn)
                                                
        if fileKind == FileKinds.SOLUTION:
            return True
        
        if fileKind == FileKinds.CHALLENGE_SOLUTION:  # weird case, only really for jupman documentation itself
            return True
            
        if len(nb.cells) > 0:            
            cell = nb.cells[0]
            
            if cell.cell_type == 'code' and ('#' + jcxt.jm.preprocess) in cell.source :                
                return True
        
    return False

    

def generate_exercise(jcxt_or_src : Union[JupmanContext, str], dest_dir='./'):
    """ Given a relative filename, generates the corresponding exercise file in dest_dir
    
        NOTE: accepts union parameter only for compat with challenges < 3.6
    """
    
    if isinstance(jcxt_or_src, str):
        import conf
        jcxt = JupmanContext(conf, jcxt_or_src, False)        
    elif isinstance(jcxt_or_src, JupmanContext):
        jcxt = jcxt_or_src
    else:
        raise JupmanError(f"Unrecognized input type: {type(jcxt_or_src)}")
        
    
    if jcxt.jpre_website:
        raise JupmanPreprocessorError("Called generate_exercise with jpre_website = True, should only be called to create physical files!")
    
    source_rel_fn = jcxt.jpre_source_filepath
    
    if not FileKinds.is_supported_ext(source_rel_fn, jcxt.jm.distrib_ext):
        raise ValueError("Exercise generation from solution not supported for file type %s" % source_rel_fn)

    kind = FileKinds.detect(source_rel_fn)

    source_abs_fn = os.path.abspath(source_rel_fn)
    source_dir = os.path.dirname(source_abs_fn)
    exercise_fn = FileKinds.exercise_from_solution(os.path.basename(source_rel_fn), jcxt.jm.distrib_ext)
    
    exercise_abs_fn = os.path.join(source_dir, exercise_fn)
    exercise_dest_fn = os.path.join(dest_dir , exercise_fn)


    njcxt = JupmanContext(jcxt, source_abs_fn, False)    
    njcxt.jpre_dest_filepath = exercise_dest_fn

    info("  Generating %s" % exercise_dest_fn)

    with open(source_abs_fn) as sol_source_f:            

        found_tag = validate_tags(jcxt, source_abs_fn)                      
        if not found_tag and not os.path.isfile(exercise_abs_fn) :
            error("There is no exercise file and couldn't find any jupman solution tag in solution file for generating exercise !" +\
                "\n  solution: %s\n  exercise: %s" % (source_abs_fn, exercise_abs_fn))                                                                      
        if not kind == FileKinds.CHALLENGE_SOLUTION and found_tag and os.path.isfile(exercise_abs_fn) :
            error("Found jupman tags in solution file but an exercise file exists already !\n  solution: %s\n  exercise: %s" % (source_abs_fn, exercise_abs_fn))
                            
        with open(exercise_dest_fn, 'w') as exercise_dest_f:
            
            if source_abs_fn.endswith('.ipynb'):
                                
                
                # note: for weird reasons nbformat does not like the sol_source_f 
                nb_node = nbformat.read(source_abs_fn, nbformat.NO_CONVERT)                    
                _sol_nb_to_ex(njcxt, nb_node)
                        
                nbformat.write(nb_node, exercise_dest_f)
            
            
            elif source_abs_fn.endswith('.py'):                                                       
                exercise_text = sol_to_ex_code(njcxt, sol_source_f.read())
                #debug("FORMATTED TEXT=\n%s" % exercise_text)
                exercise_dest_f.write(exercise_text)                    
            else:
                raise ValueError("Don't know how to translate solution to exercise for source file %s" % source_abs_fn)

def copy_code(jcxt : JupmanContext, source_dir, dest_dir, copy_solutions=False):
            
    info("Copying code %s \n    from  %s \n    to    %s" % ('and solutions' if copy_solutions else '', source_dir, dest_dir))

    # creating folders
    for dirpath, dirnames, filenames in os.walk(source_dir):
                                
        compath = os.path.commonpath([dirpath, source_dir])
        dest_subdir = os.path.join(dest_dir, dirpath[len(compath)+1:])
                        
        if not is_zip_ignored(jcxt, dest_subdir):
            if not os.path.isdir(dest_subdir) :
                info("Creating dir %s" % dest_subdir)
                os.makedirs(dest_subdir)
                    
            for source_fn in filenames:                    
                if not is_zip_ignored(jcxt, source_fn):
                    
                    source_abs_fn = os.path.join(dirpath,source_fn)
                    dest_fn = os.path.join(dest_subdir , source_fn)                           
                    fileKind = FileKinds.detect(source_fn)
                    
                    if fileKind == FileKinds.CHALLENGE_SOLUTION:
                        # challenge solutions are supposed to be generated 
                        # manually inside the jupyter notebook

                        pass
                    elif fileKind == FileKinds.SOLUTION:
                        if copy_solutions:                                             
                            njcxt = JupmanContext(jcxt, source_abs_fn, False)
                            _copy_sols(njcxt,   
                                       source_fn, 
                                       dest_fn)
                        
                        if FileKinds.is_supported_ext(  source_fn,
                                                        jcxt.jm.distrib_ext):
                            njcxt = JupmanContext(jcxt, source_abs_fn, False)                            
                            generate_exercise(njcxt,                                               
                                              dest_dir=dest_subdir)
                                        
                            
                    elif fileKind == FileKinds.TEST:                             
                        njcxt = JupmanContext(jcxt, source_abs_fn, False)
                        _copy_test(njcxt,
                                   source_fn, 
                                   dest_fn)
                    else:  # EXERCISE and OTHER
                        njcxt = JupmanContext(jcxt, source_abs_fn, False)
                        _copy_other(njcxt,
                                    source_fn,
                                    dest_fn)

def _common_files_maps(jcxt : JupmanContext, zip_name : str) -> Tuple[List[str],List[str]]:
    """ 
        Returns a tuple with deglobbed common files and their patterns
        
        zip_name:  a zip name *without* the ending '.zip'
        
        @since 3.2 Created in order to make exam.py work
    """
    
    if zip_name.endswith('zip'):
        raise JupmanError(f'zip_name must not end with .zip, found instead: {zip_name}')
    
    deglobbed_common_files = []
    deglobbed_common_files_patterns = []
    for common_path in jcxt.jm.chapter_files:                
        cur_deglobbed = glob.glob(common_path, recursive=True)       
        deglobbed_common_files.extend(cur_deglobbed)
        deglobbed_common_files_patterns.extend(
            [("^(%s)$" % x, "%s/%s" % (zip_name, x)) for x in cur_deglobbed])
    return (deglobbed_common_files, deglobbed_common_files_patterns)

def zip_folder(jcxt : JupmanContext, source_folder, renamer=None):
    """ Takes source folder and creates a zip with processed files
                    
        renamer: (optional) function which takes source folder names 
                 and gives the corresponding zip name to generate
                 WITHOUT the .zip extension
                    
    """
    if source_folder.startswith('..'):
        fatal("BAD FOLDER TO ZIP ! STARTS WITH '..'=%s" % source_folder)
    if len(source_folder.strip()) == 0:
        fatal("BAD FOLDER TO ZIP ! BLANK STRING")

    build_jupman = os.path.join(jcxt.jm.build, 'jupman')
    if renamer:
        zip_name = renamer(source_folder)
        if zip_name.endswith('.zip'):
            raise JupmanError(f"renamer function shouldn't produce names ending with .zip, got instead {zip_name}")        
    else:
        zip_name = os.path.basename(os.path.normpath(source_folder))        

    build_folder = os.path.join(build_jupman, zip_name)
    if not os.path.exists(jcxt.jm.generated):
        os.makedirs(jcxt.jm.generated)
    if os.path.exists(build_folder):
        delete_tree(build_folder, '_build')

    copy_code(jcxt, source_folder, build_folder, copy_solutions=True)

    deglobbed_common_files, deglobbed_common_files_patterns = _common_files_maps(jcxt, zip_name)
    
    info("zip_name = %s" % zip_name)            
    zip_path = os.path.join(jcxt.jm.generated, zip_name)
    zip_paths(jcxt, 
              deglobbed_common_files + [build_folder], 
              zip_path,
              patterns = deglobbed_common_files_patterns + [("^(%s)" % build_jupman,"")])
    info("Done zipping %s" % source_folder ) 

def zip_folders(jcxt : JupmanContext, selector, renamer=None):
    """ Takes source folder and creates a zip for each subfolder 
        filling it with processed files.

        selector: a glob pattern 
        renamer: (optional) function which takes source folder names 
                 and gives the corresponding zip name to generate
                 WITHOUT the .zip extension
    """
    source_folders =  glob.glob(selector)
    
    if selector.startswith('..'):
        fatal("BAD FOLDER TO ZIP ! STARTS WITH '..'=%s" % selector)
    if len(selector.strip()) == 0:
        fatal("BAD FOLDER TO ZIP ! BLANK STRING")
    if len(source_folders) == 0:
        warn("Nothing to zip for %s!" % selector)
        return
    info("Found stuff in %s , zipping them to %s" % (selector, jcxt.jm.generated))
    
    for d in source_folders:
        zip_folder(jcxt, d, renamer)
    info("Done zipping %s" % selector ) 


def latex_maketitle(jcxt, html_baseurl):
# - see this: https://tex.stackexchange.com/questions/409677/edit-1st-page-only
# - ALSO ADDED THE SUPER IMPORTANT \makeatletter according to
#    https://groups.google.com/d/msg/sphinx-users/S_ip2b-lrRs/62zkfWcODwAJ

    return r'''
        \makeatletter
        \pagestyle{empty}
        \thispagestyle{empty}
        \noindent\rule{\textwidth}{1pt}\par
            \begingroup % for PDF information dictionary
            \def\endgraf{ }\def\and{\& }%
            \pdfstringdefDisableCommands{\def\\{, }}% overwrite hyperref setup
            \hypersetup{pdfauthor={\@author}, pdftitle={\@title}}%
            \endgroup
        \begin{flushright}
            \sphinxlogo
            \py@HeaderFamily
            {\Huge \@title }\par
        ''' + r"{\itshape\large %s}\par" % unicode_to_latex( jcxt.jm.subtitle) + \
        r'''
            \vspace{25pt}
            {\Large
            \begin{tabular}[t]{c}
                \@author
            \end{tabular}}\par
            \vspace{25pt}
            \@date \par
            \py@authoraddress \par
        \end{flushright}
        \@thanks
        \setcounter{footnote}{0}
        \let\thanks\relax\let\maketitle\relax
        %\gdef\@thanks{}\gdef\@author{}\gdef\@title{}
            \vfill
            \noindent Copyright \copyright\ \the\year\ by \@author.
            \vskip 10pt
            \noindent \@title\ is available under the Creative Commons Attribution 4.0
            International License, granting you the right to copy, redistribute, modify, and
            sell it, so long as you attribute the original to \@author\ and identify any
            changes that you have made. Full terms of the license are available at:
            \vskip 10pt
            \noindent \url{http://creativecommons.org/licenses/by/4.0/}
            \vskip 10pt
            \noindent The complete book can be found online for free at:
            \vskip 10pt''' + (r'''
            \noindent \url{%s}''' % html_baseurl)


def zip_paths(jcxt : JupmanContext, rel_paths, zip_path, patterns=(), remap=None):
    """ zips provided rel_folder to file zip_path (WITHOUT .zip) !
        rel_paths MUST be relative to project root
        
        This function was needed as default python zipping machinery created weird zips 
        people couldn't open in Windows AND it is not deterministic https://github.com/DavidLeoni/jupman/issues/60
        
        - patterns is a list of tuples source regexes to dest               
        - remap is a function that takes a string and returns a string, and is applied after patterns
        
    """
    
    
    if zip_path.endswith('.zip'):
        raise ValueError("zip_path must not end with .zip ! Found instead: %s" % zip_path)

    for rel_path in rel_paths:
        abs_path = os.path.join(super_doc_dir() , rel_path)

        if not(os.path.exists(abs_path)):
            raise ValueError("Expected an existing file or folder relative to project root ! Found instead: %s" % rel_path)

    
    def write_file(fname):
        
        
        if not is_zip_ignored(jcxt, fname) :
            #info('Zipping: %s' % fname)            
            
            
            if isinstance(patterns, types.FunctionType):
                warn("zip_paths: using patterns as a function is deprecated, please use remap attribute instead")                    
                the_remap = patterns
                the_patterns = []
            else:
                the_patterns = patterns
                the_remap = remap
                
            if len(the_patterns) == 0 and the_remap == None:
                to_name = '/%s' % fname
            else:
                if len(the_patterns) > 0:
                    to_name = fname
                    for pattern, to in the_patterns:
                        try:
                            to_name = re.sub(pattern, to, to_name)
                        except Exception as ex:
                            error("Couldn't substitute pattern \n  %s\nto\n  %s\nin string\n  %s\n\n" % (pattern, to, to_name) , ex)
                                                            
                if the_remap != None:
                    to_name = the_remap(fname)

            #info('to_name = %s' % to_name)                    
            
            permission = 0o755 if os.access(fname, os.X_OK) else 0o644
            zip_info = zipfile.ZipInfo.from_file(fname, to_name)
            zip_info.date_time = (2020, 1, 1, 0, 0, 0)
            zip_info.external_attr = (stat.S_IFREG | permission) << 16
            with open(fname, "rb") as fp:
                archive.writestr(
                    zip_info,
                    fp.read(),
                    compress_type=zipfile.ZIP_DEFLATED,
                    #compresslevel=9, # python 3.7+
                )                
            

    archive = zipfile.ZipFile(zip_path + '.zip', "w")                
    
    for rel_path in sorted(rel_paths):

        if os.path.isdir(rel_path):            
            for dirname, dirs, files in sorted(os.walk(rel_path), key=lambda t: t[0]):
                dirNamePrefix = dirname + "/*"                
                filenames = glob.glob(dirNamePrefix)                    
                for fname in sorted(filenames):
                    if os.path.isfile(fname):
                        write_file(fname)
        elif os.path.isfile(rel_path):
            info('Writing %s' % rel_path)
            write_file(rel_path)
        else:
            raise ValueError("Don't know how to handle %s" % rel_path)
    archive.close()
        
    info("Wrote %s.zip" % zip_path)
    
    
#lower to heavier
_chapter_files_weight = [r'(?<!-sol)\.ipynb$', 
                         r'-sol\.ipynb$', 
                         r'-chal\.ipynb$', 
                         r'(?<!(_sol))(?<!(_test))\.py$', 
                         r'.*_test\.py$', 
                         r'.*_sol\.py$']
"""
@since 3.6
"""

def _compare_chapter_files(a : str, b : str) -> int:
    """
    
    Returns:
    
        a > b : 1
        a == b: 0
        a < b: -1 
    
    according to example ordering in _make_preamble_filelist
    
    @since 3.6                    
    """    
    
    if a == b:
        return 0
        
    ws = _chapter_files_weight
    wa = len(ws)
    wb = len(ws)    
    
    #if a.endswith('.ipynb') and b.endswith(('.ipynb'):
    kind_a, prefix_a, ending_a, ext_a = FileKinds.parse(a)
    kind_b, prefix_b, ending_b, ext_b = FileKinds.parse(b)
        
    def scomp(ma,mb):
        if ma > mb:
            return 1
        elif ma == mb:
            return 0
        else:
            return -1
    
    def impcomp(e1, e2, r):
        
        if ext_a == e1:
            if ext_b == e1:
                if prefix_a == prefix_b:
                    if kind_a == FileKinds.SOLUTION:                    
                        return 1  # always at the bottom
                    elif kind_a == FileKinds.TEST:
                        if kind_b == FileKinds.SOLUTION:
                            return -1
                        else:
                            return 1                
                    else:
                        return -1
                else:                
                    return scomp(prefix_a, prefix_b)
            elif ext_b == e2:
                return r
            else:
                return -1
        else:
            return None
    
    ret = impcomp('ipynb', 'py', -1)
    if ret != None:
        return ret
    else:
        ret = impcomp('py', 'ipynb', 1)
        if ret != None:
            return ret
        elif ext_b == 'py' or ext_b == 'ipynb':
            return 1
        else:
            return scomp(a, b)   
    
    
    
def _make_preamble_filelist(jcxt, 
                            zip_filepath : str,                             
                            marked : Iterable[str] = PREAMBLE_MARKED,
                            ignored : Iterable[str] = PREAMBLE_IGNORED) -> List[str]:
    """ 
    
    Given an existing zip file path, returns a list of files to show in tutorials.                
                
    marked: list of files to show highlighted (files subfolders cannot be marked), first one is 
            the one the user should open first). Special value 'CURRENT' represents 
            current notebook destination (jcxt.jpre_dest_filepath)
    ignored: ignored paths, supports glob
    
    Example (indentations are just visual aid)
           
       [(0, example-chapter)
            (1, examples1)            <--- directories first
                (2, people.csv)
                
            (1, examples2)            <--- alphabetically sorted
                (2, jobs.csv)
                (2, salary.csv)                
                
            (1, lab.ipynb),           <--- first notebooks 
            (1, lab_sol.ipynb),      
            (1, work.ipynb, *),       <--- manually marked notebooks
            (1, work_sol.ipynb),        
            (1, lists.py),            <--- then .py          
            (1, lists_sol.py)           
            (1, lists_test.py),         
            (1, trees.py),                      
            (1, trees_sol.py)           
            (1, trees_test.py),                                              
            (1, data1.csv, *),        <--- then other main files like data  
            (1, data2.csv),                                                             
            (1, jupman.py)]           <--- finally jm.chapter_files         
        
                        
    Note: it would be better to determine a zip content by looking at the source folder,      
    but as of 3.6 it's not worth the effort, see  https://github.com/DavidLeoni/jupman/issues/115        
    
    @since 3.6                    
    """
    
    debug(f'Reading {zip_filepath }')
    
    if not zip_filepath.endswith('.zip'):
        raise JupmanPreprocessorError(f"Provided zip filepath must end with .zip, found instead: {zip_filepath}")
    
    if not os.path.isfile(zip_filepath):
        raise JupmanNotFoundError(f"Provided zip filepath doesn't exist: {zip_filepath}")
    
    root_folder = os.path.basename(zip_filepath)[:-4]
    debug(f"root_folder: {root_folder}")
    if not root_folder:
        raise JupmanPreprocessorError("root_folder empty, something went wrong!")
    
    dest_filename = os.path.basename(jcxt.jpre_dest_filepath)
    debug(f"dest_filename: {dest_filename}")                
    
    if not dest_filename.endswith('.ipynb'):
        raise JupmanPreprocessorError(f"Expected a .ipynb file as jcxt.jpre_dest_filepath, found instead {jcxt.jpre_dest_filepath}")
        
    with zipfile.ZipFile(zip_filepath) as zf:        
        zdp = f"{root_folder}/{dest_filename}"
        if zdp  not in zf.namelist():
            raise JupmanNotFoundError(f"Couldn't find :\n {zdp} in zip:\n{zip_filepath}")
        
    from pathlib import Path
    shrinked_zip_files = []
    with zipfile.ZipFile(zip_filepath) as zf:        
        for filepath in zf.namelist():
            p  = Path(filepath)               
            if len(p.parts) <= 1:
                raise JupmanPreprocessorError(f"Files in a chapter zip should always be in a subfolder, found instead {filepath}")
            
            if root_folder != p.parts[0]:
                raise JupmanPreprocessorError(f"Files in a chapter zip should always be in a subfolder named as the zip, found instead {filepath}")
            shrinked_zip_files.append(os.path.join(*p.parts[1:]))
    
    marked_set = set()                   
    for tf in marked:        
                
        if tf == 'CURRENT':
            #NOTE: this is supposed to be in the chapter folder at level 1            
            el = dest_filename
        else: 
            el = tf
                
        if el not in shrinked_zip_files: 
            raise JupmanNotFoundError(f"Couldn't find provided marked file: {el}")
        if len(Path(el).parts) > 2:
            raise JupmanUnsupportedError(f"Marked files can only have 1 depth level, found instead: {el}")

        marked_set.add(el)
    

    dirs = []
                                
    filtered_set = set()
    nested_set = set()
    main_set = set()
    last_set = set()
            
    for dest_fn in sorted(shrinked_zip_files):
        
        if not is_zip_ignored(jcxt, dest_fn):            
            spec = pathspec.PathSpec.from_lines('gitwildmatch', ignored)
            if not spec.match_file(dest_fn):                                
                found = False                            
                fileKind = FileKinds.detect(dest_fn)
                
                if dest_fn not in filtered_set:
                    filtered_set.add(dest_fn)
                    if len(Path(dest_fn).parts) > 1:
                        nested_set.add(dest_fn)
                    elif pathspec.PathSpec.from_lines('gitwildmatch', jcxt.jm.chapter_files).match_file(dest_fn):
                        last_set.add(dest_fn)
                    else:
                        main_set.add(dest_fn)


    ret = [(0, root_folder)]
    
    prev_path = ()
    
    def augment_ret(j, folders_path):
        for k in range(j, len(folders_path)):
            if fp in marked_set:
                ret.append( (k+1, folders_path[k], '*') )
            else:
                ret.append( (k+1, folders_path[k]) )
                            
    for fp in sorted(nested_set):     
        p = Path(fp)
        folders_path = p.parts[:-1]
        
        if folders_path != prev_path:
            j = 0
            scan = True
            while j < len(folders_path) and scan:
                if j < len(prev_path):
                    if folders_path[j] != prev_path[j]:
                        augment_ret(j,folders_path)                            
                        scan = False
                else:
                    augment_ret(j,folders_path)
                    scan = False
                j += 1            
            prev_path = folders_path             
        
        ret.append( (len(folders_path)+1, p.parts[-1]) )

    from functools import cmp_to_key
    ret.extend( ((1,fp, '*') if fp in marked_set else (1,fp) for fp in sorted(main_set, key=cmp_to_key(_compare_chapter_files))) )
    ret.extend( ((1,fp, '*') if fp in marked_set else (1,fp) for fp in sorted(last_set, key=cmp_to_key(_compare_chapter_files))) )
    
    return ret
