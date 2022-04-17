import sys
sys.path.append('../')
import jupman
import local


def add(x,y):   
    #jupman-raise
    return x + y
    #/jupman-raise

def sub(x,y):
    return help_func(x,y) 

#jupman-strip
# stripped stuff is not present in exercises
def help_func(x,y):
    return x - y
#/jupman-strip


#jupman-purge
# purged stuff not present in exercises nor in solutions
def disappear(x):
    return x 
#/jupman-purge


# everything after next comment will be discarded

# write here

def f(x):
    return x + 1