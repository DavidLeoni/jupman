

class MyClass:

    """ 
        This class does... stuff
    """
    def do_something(self):
        #jupman-raise
        print("Doing something")
        #/jupman-raise

 
    def do_something_else(self):
        #jupman-raise
        print("Doing something else")
        helper(5)
        #/jupman-raise
        
#jupman-strip
def helper(x):
    return x + 1
#/jupman-strip


# templating in code
# source file: _JUPMAN_.jpre_source_filepath
# dest file: _JUPMAN_.jpre_dest_filepath

print("Written by _JUPMAN_.author")
print("Intendend for _JUPMAN_.jm.manual")
