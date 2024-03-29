
# Changelog

Jupman: A template for online manuals made with Jupyter notebooks.

[jupman.softpython.org](https://jupman.softpython.org)


## July 9th, 2023 - 3.5.7

Added:
- Softpython theme eye candy #122
    - softpython-theme-textures.css with manually embedded base64 images
    - jupman-alert-principle in jupman-web.css as backbone for commandments
- logo, favicon #123
- explicilty stated all dependencies in requirements-build.txt, added create_env script #82
- improved manual

Fixed:
- relative paths in cell outputs for zips #119
- now using relative js and css imports in jupman.init  #117
- Python Tutor: 
    - now shows unnest data structures by default #132
    - now shows in cloned cells #126 (changed stable ids #107)
    - sets are now correctly displaying with grey header  #125
    - tutor Visual Studio Code no longer appears with grey text #136    

Removed:
- `_private/README.md`


## August 11th, 2022 - 3.5.4

- Python Tutor:
  - added credits #111
  - visualized vertical separator bar #110 
  - fixed red arrow misalignment #105
  - stable ids #107
  - removed 'Customize visualization' #108
- Github actions: automatically build themed version #100
- SoftPython theme #92: various fixes
- Fixed relative html a, img with attributes in markdown not working in zip: #113


## June 4th 2022 - 3.5

- generated html can be really used offline #96, also fixes wrong math symbols with local build #3
- automated testing on github actions #99
- virtual env install, pinpointed build depenedencies #82
- fixed text overflow on smartphones #94,  fixed softpython theme flag
- github actions: always reset html output #98


## April 28th 2022 - 3.4

- fixed softpython theme font size #92
- restructured manual

## February 25th 2022 - 3.3

Implemented: 

- jupman-preprocess #64 
- big docs support #77
- Challenges support (suboptimal but usable) #56 
- jupman-purge #59
- jupman.draw_text for #66
- jupman.save_py function
- jupman.get_doc as nice way to print function documentation #68 
- jupman.draw_text to show some ASCII characters in local build #66 
- jupman.mem_limit for Linux #62 

- Home link should point to index.html #71 
- optional parameter conf to jmt.init
- deterministic zip #60 (requires python 3.7)

Fixed:

- Notebook validation failed: Non-unique cell id error #78 
- exam pdf build breaks when using images #61 

Defined:

- how to use custom anchors #80 
- how to have single pages like References at menu bottom #70 


## October 17th 2020 - 3.2

- added optional build on Github Actions
- solutions are finally hidden on the website, with a click-to-show button!
- introduced generic jupman-togglable and specific jupman-sol CSS classes
- improved menu navigation
- added softpython theme
- images are now shown centered in HTML
- moved to jupman.softpython.org
- fixed write here tag not preserving the line
- deprecated jupman_tools.ignore_spaces in favor of tag_regex
- updated nbsphinx to 0.7.1
- updated sphinx_rtd_theme to 0.4.3
- updated sphinx to 2.3.1
- updated pygments to 2.7.1

## January 16th 2020 - 3.1

- removed jupman.init root parameter
- bugfixes
- upgraded nbsphinx from 0.3.4 to 0.5.0
- upgraded sphinx_rtd_theme from 0.2.5b1 to 0.4.3
- upgraded sphinx from 1.7.6 to 2.3.1
- upgraded recommonmark from 0.4.0 to 0.6.0

## December 29th 2019 - 3.0

- much simplified folder structure 
  - [Issue 33](https://github.com/DavidLeoni/jupman/issues/33)

- removed solutions from header requirement 
  - [Issue 32](https://github.com/DavidLeoni/jupman/issues/32)

- introduced tests (pytest, hypothesis)
- removed old_news in favor of changelog.md
- Latex:
    - much better PDF cover
    - using xelatex
    - set up unicode mappings
- several fixes

## September 24th 2018 - 2.0

- now using index.ipynb as home. Hurray !

## September 19th 2018 - 1.0

- fixed build.py
- added html templates examples
- cleaned toc (was showing too much when loading)


## August 26th 2018 - 0.9

- implemented generation of exercises from solutions
  [Issue 14(https://github.com/DavidLeoni/jupman/issues/14)
- reverted to old jupman.init() code
  [Issue 12](https://github.com/DavidLeoni/jupman/issues/12)

## August 12th 2018 - 0.8

- Prepended all functions in jupman.py with `jupman_`

- replaced index with proper homepage. 
  see [Issue 11](https://github.com/DavidLeoni/jupman/issues/11)
  
  - from now on you need home.ipynb file, because replacing index.rst is a nightmare! 
  - new index.rst is just a placeholder which simply redirects to home.html. Do not modify it.
  - put the toctree in toc.rst
  
- exercises ipynb can now stay in exercises/ folder; when exercises are zipped,
  jupman automatically adds to the zip the required site files. 
  see [Issue 12](https://github.com/DavidLeoni/jupman/issues/12)
  
- Tried %run at beginning of notebooks, without much satisfaction
  (see discussion in [Issue 12](https://github.com/DavidLeoni/jupman/issues/12)): 
  
- disabled toc by default in html files. To enable it, in python use `%run -i ../../jupman --toc`
- renamed past-exams directory from 'past-exams' to 'exams'
- created `info`, `error`, `warn`, `fatal` functions to `conf.py`
- introduced new variable `exercise_common_files` in `conf.py` for common files to be zipped
- added pages `exam-project` , `markdown` , `project-ideas`, 
- added `cc-by.png`
- renamed `changelog.txt` to `changelog.md`
- now using templates with curly brackets in in templating, like `_JM_{some_property}`
- jupman.js : now when manually saving html in Jupyter, resulting html correctly hides cells
- Fixes https://github.com/DavidLeoni/jupman/issues/2 : 
  now toc is present in local build for pdfs 

## August 3rd 2018 - 0.7

- added jupman.py pytut() for displaying Python tutor in the cells
- added  jupman.py toc=False option to jupman.py init to disable toc
- removed  jupman.pyuseless networkx import from 

- fixed usage indentation
- added changelog.txt

