import file

# 10
# Python
import sys
sys.path.append('../../')
import jupman

# this is a solution, jupman tags should get suppressed:

# work!
#jupman-raise
print('hi')
#/jupman-raise

# removed in exercise, kept in solution
#jupman-strip
y = "stripped!"
#/jupman-strip

# removed in exercise, removed in solution
#jupman-purge
y = "purged!"
#/jupman-purge

# templating in code
# source file: _JUPMAN_.jpre_source_filepath
# dest file: _JUPMAN_.jpre_dest_filepath

print("Written by _JUPMAN_.author")
print("Intendend for _JUPMAN_.jm.manual")
