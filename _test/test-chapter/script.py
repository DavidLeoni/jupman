# 10
# Python
import sys
sys.path.append('../../')
import jupman

# this is not a solution, jupman tags shouln't get processed:
#jupman-raise

# templating in code should still be processed:
# source file: _JUPMAN_.jpre_source_filepath
# dest file: _JUPMAN_.jpre_dest_filepath

print("Written by _JUPMAN_.author")
print("Intendend for _JUPMAN_.jm.manual")
