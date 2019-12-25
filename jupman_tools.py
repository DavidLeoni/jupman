import zipfile
from pylatexenc.latexencode import unicode_to_latex
from enum import Enum
import re
import os
import shutil
import inspect
import types
import glob
    

def fatal(msg, ex=None):
    """ Prints error and exits (halts program execution immediatly)
    """
    if ex == None:
        exMsg = ""
    else:
        exMsg = " \n  %s" % repr(ex)
    info("\n\n    FATAL ERROR! %s%s\n\n" % (msg,exMsg))
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
    info("\n\n    FATAL ERROR! %s%s\n\n" % (msg,exMsg))
    raise the_ex
    
def info(msg=""):
    print("  %s" % msg)

def warn(msg):
    print("\n\n   WARNING: %s" % msg)

def debug(msg=""):
    print("  DEBUG=%s" % msg) 
    
def parse_date(ld):
    try:
        return datetime.datetime.strptime( str(ld), "%Y-%m-%d")
    except:
        raise Exception("NEED FORMAT 'yyyy-mm-dd', GOT INSTEAD: '%s" % ld)

    
def parse_date_str(ld):
    """
        NOTE: returns a string 
    """
    return str(parse_date(ld)).replace(' 00:00:00','')
    

    
def super_doc_dir():
    return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

def detect_release():
    try:
        from subprocess import check_output
        release = check_output(['git', 'describe', '--tags', '--always'])
        release = release.decode().strip()
        if not '.' in release[0]:
            release = '0.1.0'
            #info("Couldn't find git tag, defaulting to: %s" % release)
        #else:    
        #   info("Detected release from git: %s" % release)
    except Exception:
        release = '0.1.0'
        #info("Couldn't find git version, defaulting to %s" % release)

    return release

def get_version(release):
    """ Given x.y.z-something, return x.y  """

    sl = release.split(".")
    return  '%s.%s' % (sl[0], sl[1])


def expand_JM(source, target, exam_date, conf):
    d = parse_date(exam_date)
    sourcef = open(source, "r")
    s = sourcef.read()
    s = s.replace('_JM_{exam.date}', exam_date )
    s = s.replace('_JM_{exam.date_human}', d.strftime('%A %d, %B %Y') )
    for k in conf.__dict__:
        s = s.replace('_JM_{conf.' + k + '}', str(conf.__dict__[k]))
    for k in conf.jmc.__dict__:
        s = s.replace('_JM_{conf.jm.' + k + '}', str(conf.jm.__dict__[k]))
    p = re.compile(r'_JM_\{[a-zA-Z][\w\.]*\}')
    if p.search(s):
        warn("FOUND _JM_ macros which couldn't be expanded!")
        print("               file: %s" % source)
        print("\n                 ".join(p.findall(s)))
        print("")
    destf = open(target, 'w')    
    destf.write(s)

class FileKinds(Enum):
    SOLUTION = 1
    EXERCISE = 2
    TEST = 3
    OTHER = 4

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
    def detect(fname):
        l = fname.split(".")
        if len(l) > 0:
            ext = l[-1]
        else:
            ext = ''
        if fname.endswith(FileKinds.sep(ext) + "solution" + '.' + ext):
            return FileKinds.SOLUTION            
        elif fname.endswith(FileKinds.sep(ext) + "exercise" + '.' + ext):
            return FileKinds.EXERCISE 
        elif fname.endswith("_test.py") :
            return FileKinds.TEST        
        else:
            return FileKinds.OTHER

    @staticmethod
    def check_ext(fname, supp_ext):
        if not FileKinds.is_supported_ext(fname, supp_ext):
            raise Exception("%s extension is not supported. Valid values are: %s" % (fname, supp_ext))
        
    @staticmethod        
    def exercise(radix, ext, supp_ext):      
        FileKinds.check_ext(ext,supp_ext)
        return radix + FileKinds.sep(ext) + 'exercise.' + ext

    @staticmethod
    def exercise_from_solution(fname, supp_ext):
        FileKinds.check_ext(fname, supp_ext)
        ext = fname.split(".")[-1]
               
        return fname.replace(FileKinds.sep(ext) + "solution." + ext, FileKinds.sep(ext) + "exercise." + ext)
        
    @staticmethod
    def solution(radix, ext, supp_ext):
        FileKinds.check_ext(ext, supp_ext)
        return radix + FileKinds.sep(ext) + 'solution.' + ext

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


def delete_tree(path, path_check):
    """ Deletes a directory, checking you are deleting what you really want

        path: the path to delete as a string
        path_check: the beginning of the path to delete, as a string
    """
    print("Cleaning %s  ..." % path)
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
    print("Cleaning %s  ..." % path)
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

def ignore_spaces(pattern):
    """ Return a regex string which ignores extra spaces in s and newline after """
    if len(pattern) == 0:
        raise ValueError("Expect a non-empty string !")
    removed_spaces = r'\s+'.join(pattern.split())
    return r"(?s)\s*(%s)(.*)" % removed_spaces

class Jupman:
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

        self.chapter_common_files = ['jupman.py', 'my_lib.py', 'img/cc-by.png', 
                                
                            '_static/js/jupman.js',  # these files are injected when you call jupman.init()
                            '_static/css/jupman.css', 
                            '_static/js/toc.js']
        """ Common files for exercise and exams as paths. Paths are intended relative to the project root. Globs like /**/* are allowed."""

        self.chapters =  ['*/']
        self.chapters_exclude =  ['[^_]*/','exams/', 'project/']

        self.ipynb_solution = "solutions"
        """ words used in ipynb files - you might want to translate these in your language. Use plural."""

        self.ipynb_exercise = "exercises"
        """ words used in ipynb files - you might want to translate these in your language. Use plural."""        

        self.write_solution_here = ignore_spaces("# write here")
        """ the string is not just a translation, it's also a command that   when 
        building the exercises removes the content after it in the code cell it is 
        contained in. If the user inserts extra spaces the phrase will be recognized 
        anyway"""

        self.solution = ignore_spaces("# SOLUTION")
        """ #NOTE: the string is not just a translation, it's also a command
            that  when building the exercises completely removes the content of the cell 
            it is contained in (solution comment included). If the user inserts extra spaces the phrase will be recognized anyway"""


        self.markdown_answer = ignore_spaces("**ANSWER**:")
        """NOTE: the following string is not just a translation, it's also a command that   when building the exercises
              removes the content after it in the markdown cell it is contained in
        """

        #pattern as in ipynb json file - note markdown has no output in ipynb
        self.ipynb_title = r"(\s*#.*)(" + self.ipynb_solution + r")"


        self.zip_ignored = ['__pycache__', '**.ipynb_checkpoints', '.pyc', '.cache', '.pytest_cache', '.vscode',]

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

        self.raise_exc_code = "raise Exception('TODO IMPLEMENT ME !')"
        """ WARNING: this string can end end up in a .ipynb json, so it must be a valid JSON string  ! Be careful with the double quotes and \n  !!
        """

        self.tags = [self.raise_exc, self.strip]

        self.supported_distib_ext = ['py', 'ipynb']

    def zip_ignored_file(self, fname):
        
        for i in self.zip_ignored:
            if fname.find(i) != -1:
                return True


    def raise_exc_pattern(self):
        return re.compile(tag_start(self.raise_exc) + '.*?' + tag_end(self.raise_exc), flags=re.DOTALL)

    def strip_pattern(self):
        return re.compile(tag_start(self.strip) + '.*?' + tag_end(self.strip), flags=re.DOTALL)

    def get_exercise_folders(self):
        ret = []
        for p in self.chapters:
            for r in glob.glob(p):
                if r not in ret:
                    ret.append(r)
        for p in self.chapters_exclude:
            for r in glob.glob(p):
                if r in ret:
                    ret.remove(r)
        return ret

    def get_exam_student_folder(self, ld):
        parse_date(ld)
        return '%s-%s-FIRSTNAME-LASTNAME-ID' % (self.filename,ld)    


    def solution_to_exercise_text(self, solution_text):
                            
        formatted_text = re.sub(self.raise_exc_pattern(), self.raise_exc_code, solution_text)                    
        formatted_text = re.sub(self.strip_pattern(), '', formatted_text)
        formatted_text = re.sub(self.write_solution_here, r'\1\n\n', formatted_text)
        return formatted_text            

        
    def validate_tags(self, text, fname):
        tag_starts = {}
        tag_ends = {}

        for tag in self.tags:
            tag_starts[tag] = text.count(tag_start(tag))                                           
            tag_ends[tag] = text.count(tag_end(tag))

        for tag in tag_starts:
            if tag not in tag_ends or tag_starts[tag] != tag_ends[tag] :
                raise ValueError("Missing final tag %s in %s" % (tag_end(tag), fname) )

        for tag in tag_ends:
            if tag not in tag_starts or tag_starts[tag] != tag_ends[tag] :
                raise ValueError("Missing initial tag %s in %s" % (tag_start(tag), fname) )
        
        write_solution_here_count = len(re.compile(self.write_solution_here).findall(text))
        solution_count = len(re.compile(self.solution).findall(text))
        
        return sum(tag_starts.values()) + write_solution_here_count + solution_count > 0



    def copy_sols(self, source_filename, source_abs_filename, dest_filename):
        if FileKinds.is_supported_ext(source_filename, self.supported_distib_ext):
            info("Stripping jupman tags from %s " % source_filename)
            with open(source_abs_filename) as sol_source_f:
                text = sol_source_f.read()
                stripped_text = text
                for tag in self.tags:

                    stripped_text = stripped_text \
                                    .replace(tag_start(tag), '') \
                                    .replace(tag_end(tag), '')

                with open(dest_filename, 'w') as solution_dest_f:
                    solution_dest_f.write(stripped_text)

        else: # solution format not supported                           
            info("Writing %s" % source_filename)
            shutil.copy(source_abs_filename, dest_filename)
            

    def generate_exercise(self, source_filename, source_abs_filename, dirpath, structure):
        exercise_fname = FileKinds.exercise_from_solution(source_filename, self.supported_distib_ext)
        exercise_abs_filename = os.path.join(dirpath, exercise_fname)
        exercise_dest_filename = os.path.join(structure , exercise_fname)


        if FileKinds.is_supported_ext(source_filename, self.supported_distib_ext):

            with open(source_abs_filename) as sol_source_f:
                solution_text = sol_source_f.read()                                

                found_tag = self.validate_tags(solution_text, source_abs_filename)                                                                                

                if found_tag:

                    if os.path.isfile(exercise_abs_filename) :
                        raise Exception("Found jupman tags in solution file but an exercise file exists already !\n  solution: %s\n  exercise: %s" % (source_abs_filename, exercise_abs_filename))

                    info('Found jupman tags in solution file, going to derive from solution exercise file %s' % exercise_fname )                                    

                                                            
                    with open(exercise_dest_filename, 'w') as exercise_dest_f:
                        
                        
                        if source_abs_filename.endswith('.ipynb'):
                            
                            import nbformat
                            # note: for weird reasons nbformat does not like the sol_source_f 
                            nb_ex = nbformat.read(source_abs_filename, nbformat.NO_CONVERT)
                                                                            
                            found_title = False
                            # look for title
                            for cell in nb_ex.cells:
                                if cell.cell_type == "markdown":
                                    if re.compile(self.ipynb_title).search(cell.source):
                                        found_title = True
                                        cell.source = re.sub(re.compile(self.ipynb_title), 
                                                    r"\1" + self.ipynb_exercise, cell.source) 
                                        break
                            
                            if not found_title:
                                error("Couldn't find title in file: \n   %s\nThere should be a markdown cell beginning with text (note string '%s' is mandatory)\n# bla bla %s" % (source_abs_filename, self.ipynb_solution, self.ipynb_solution))
        
        
                            # look for tags
                            for cell in nb_ex.cells:
                                if cell.cell_type == "code":
                                    if cell.source.strip().startswith(self.solution):
                                        cell.source = " " 
                                    else:
                                        cell.source = self.solution_to_exercise_text(cell.source)
                                if cell.cell_type == "markdown":
                                    if cell.source.strip().startswith(self.markdown_answer):                                  
                                        cell.source = " " # space, otherwise it shows 'Type markdown or latex'                               
                                    
                            nbformat.write(nb_ex, exercise_dest_f)
                        
                        else:
                            
                            exercise_text = self.solution_to_exercise_text(solution_text)
                            #debug("FORMATTED TEXT=\n%s" % exercise_text)
                            exercise_dest_f.write(exercise_text)                    
                                                                    
                else:
                    if not os.path.isfile(exercise_abs_filename) :
                        error("There is no exercise file and couldn't find any jupman tag in solution file for generating exercise !" +\
                            "\n  solution: %s\n  exercise: %s" % (source_abs_filename, exercise_abs_filename))
                        
    def copy_code(self, source_dir, dest_dir, copy_test=True, copy_solutions=False):
        
        
        info("  Copying exercises %s \n      from  %s \n      to    %s" % ('and solutions' if copy_solutions else '', source_dir, dest_dir))
        # creating folders
        for dirpath, dirnames, filenames in os.walk(source_dir):
            structure = os.path.join(dest_dir, dirpath[len(source_dir):])
            
            if not self.zip_ignored_file(structure):
                if not os.path.isdir(structure) :
                    print("Creating dir %s" % structure)
                    os.makedirs(structure)

                for source_filename in filenames:
                                    
                    if not self.zip_ignored_file(source_filename):
                        
                        source_abs_filename = os.path.join(dirpath,source_filename)
                        dest_filename = os.path.join(structure , source_filename) 

                        

                        fileKind = FileKinds.detect(source_filename)
                        
                        if fileKind == FileKinds.SOLUTION:                  
                            
                            if copy_solutions:                                           
                                self.copy_sols(source_filename, source_abs_filename, dest_filename)
                            
                            if FileKinds.is_supported_ext(  source_filename,      
                                                            self.supported_distib_ext):
                                self.generate_exercise(source_filename, source_abs_filename, dirpath, structure)    
                                            
                                
                        elif fileKind == FileKinds.TEST:
                            with open(source_abs_filename, encoding='utf-8') as source_f:
                                data=source_f.read().replace('_solution ', '_exercise ')
                                info('Writing patched test %s' % source_filename) 
                                with open(dest_filename, 'w', encoding='utf-8') as dest_f:
                                    dest_f.write(data)                         
                        else:  # EXERCISE and OTHER
                            info("  Writing %s " % source_filename)
                            shutil.copy(source_abs_filename, dest_filename)


    def zip_folder(self, source_folder, prefix='', suffix=''):
        """ Takes source folder and creates a zip with processed files
        """
        if source_folder.startswith('..'):
            fatal("BAD FOLDER TO ZIP ! STARTS WITH '..'=%s" % source_folder)
        if len(source_folder.strip()) == 0:
            fatal("BAD FOLDER TO ZIP ! BLANK STRING")

        build_jupman = os.path.join(self.build, 'jupman')
        build_folder = os.path.join(build_jupman, source_folder)
        if not os.path.exists(self.generated):
            os.makedirs(self.generated)
        if os.path.exists(build_folder):
            delete_tree(build_folder, '_build')
        
        self.copy_code(source_folder, build_folder, copy_test=True, copy_solutions=True)

        deglobbed_common_files = []
        deglobbed_common_files_patterns = []
        for common_path in self.chapter_common_files:                
            cur_deglobbed = glob.glob(common_path, recursive=True)       
            deglobbed_common_files.extend(cur_deglobbed)
            deglobbed_common_files_patterns.extend(
                [("^(%s)$" % x, "%s/%s" % (source_folder, x)) for x in cur_deglobbed])

        dir_name= os.path.basename(os.path.normpath(source_folder))
        info("dir_name = %s" % dir_name)
        zip_name = prefix + dir_name + suffix
        zip_path = os.path.join(self.generated, zip_name)
        self.zip_paths( deglobbed_common_files + [source_folder], 
                        zip_path,
                        patterns= deglobbed_common_files_patterns + [("^(%s)" % build_jupman,"")])
        info("Done zipping %s" % source_folder ) 

    def zip_folders(self, source_folder, prefix='', suffix=''):
        """ Takes source folder and creates a zip for each subfolder 
            filling it with processed files
        """
        source_folders =  glob.glob(source_folder + "/*/")
        
        if source_folder.startswith('..'):
            fatal("BAD FOLDER TO ZIP ! STARTS WITH '..'=%s" % source_folder)
        if len(source_folder.strip()) == 0:
            fatal("BAD FOLDER TO ZIP ! BLANK STRING")
        if len(source_folders) == 0:
            warn("Nothing to zip for %s!" % source_folder)
            return
        info("Found stuff in %s , zipping them to %s" % (source_folder, self.generated))
        
        for d in source_folders:
            self.zip_folder( d, prefix, suffix)
        info("Done zipping subfolders of %s" % source_folder ) 


    def latex_maketitle(self, html_baseurl):
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
            ''' + r"{\itshape\large %s}\par" % unicode_to_latex( self.subtitle) + \
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


    def zip_paths(self, rel_paths, zip_path, patterns=[]):
        """ zips provided rel_folder to file zip_path (WITHOUT .zip) !
            rel_paths MUST be relative to project root
            
            This function was needed as default python zipping machinery created weird zips 
            people couldn't open in Windows
            
            patterns can be:
            - a list of tuples source regexes to dest 
            - a function that takes a string and returns a string
            
        """
        
        
        if zip_path.endswith('.zip'):
            raise ValueError("zip_path must not end with .zip ! Found instead: %s" % zip_path)

        for rel_path in rel_paths:
            abs_path = os.path.join(super_doc_dir() , rel_path)

            if not(os.path.exists(abs_path)):
                raise ValueError("Expected an existing file or folder relative to project root ! Found instead: %s" % rel_path)

        
        def write_file(fname):
            
            
            if not self.zip_ignored_file(fname) :
                #info('Zipping: %s' % fname)            
                
                
                if isinstance(patterns, (list,)):
                    if len(patterns) > 0:
                        to_name = fname
                        for pattern, to in patterns:    
                            try:
                                to_name = re.sub(pattern, to, to_name)
                            except Exception as ex:
                                error("Couldn't substitute pattern \n  %s\nto\n  %s\nin string\n  %s\n\n" % (pattern, to, to_name) , ex)
                    else:
                        to_name = '/%s' % fname
                        
                elif isinstance(patterns, types.FunctionType):
                    to_name = patterns(fname)
                else:
                    error('Unknown patterns type %s' % type(patterns))

                #info('to_name = %s' % to_name)                    
                    
                archive.write(fname, to_name, zipfile.ZIP_DEFLATED)

        archive = zipfile.ZipFile(zip_path + '.zip', "w")
        
        for rel_path in rel_paths:

            if os.path.isdir(rel_path):            
                for dirname, dirs, files in os.walk(rel_path):                    
                    dirNamePrefix = dirname + "/*"                
                    filenames = glob.glob(dirNamePrefix)                    
                    for fname in filenames:
                        if os.path.isfile(fname):
                            write_file(fname)
            elif os.path.isfile(rel_path):
                info('Writing %s' % rel_path)
                write_file(rel_path)
            else:
                raise ValueError("Don't know how to handle %s" % rel_path)
        archive.close()
            
        info("Wrote %s" % zip_path)
