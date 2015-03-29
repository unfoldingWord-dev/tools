
import sys
import os


def get_adm_dir():
    """Return the name of Subversion's administrative directory,
	adjusted for the SVN_ASP_DOT_NET_HACK environment variable.  See
	<http://svn.collab.net/repos/svn/trunk/notes/asp-dot-net-hack.txt>
	for details."""
    return os.environ.has_key("SVN_ASP_DOT_NET_HACK") and "_svn" or ".svn"

#print get_adm_dir()

class clean_folders:
    
    root_path = ""
    total = 0

    def do_it(self):
        path_to_clean = raw_input("Path to clean: ")
        if path_to_clean == "":
            print "You canceled."
        else:
            format_nbr = ""
            self.root_path = path_to_clean
            os.path.walk(self.root_path, self.remove_dirs, format_nbr)
            print "FINISHED " + str(self.total) + "!!!"

    def write_dirs(self, format_nbr, dirname, paths):
        for path in paths:
            nme = str(path)
            if nme == ".svn":
                print dirname + "\\" + path

    def remove_dirs(self, format_nbr, dirname, paths):
        for path in paths:
            nme = str(path)
            
            if nme == "_svn" or nme == ".svn" or nme == ".hg":
                print dirname + "\\" + nme
                self.removeall(dirname + "\\" + nme)
                try:
                    os.removedirs(dirname + "\\" + nme)
                except:
                    if os.path.exists(dirname + "\\" + nme):
                        print "Could not remove " + dirname + "\\" + nme

##            else:
##                # remove *.vb, *.resx, and _directories
##                fullpath=os.path.join(dirname, path)
##                if os.path.isfile(fullpath):
##                    if str(fullpath).endswith(".rar") or str(fullpath).endswith(".pdb") or str(fullpath).endswith("AZ Delta.ssdb"):
##                        f=os.remove
##                        self.rmgeneric(fullpath, f)
##
##                elif os.path.isdir(fullpath):
##                    if nme.startswith("_") or nme.endswith(".scc") or nme.lower() == "bin" or nme.lower() == "obj":
##                        self.removeall(fullpath)
##                        f=os.removedirs
##                        self.rmgeneric(fullpath, f)
                        
                    
                
    def removeall(self, path):

        if not os.path.isdir(path):
            return

        files=os.listdir(path)

        for x in files:
            fullpath=os.path.join(path, x)
            if os.path.isfile(fullpath):
                f=os.remove
                self.rmgeneric(fullpath, f)
            elif os.path.isdir(fullpath):
                self.removeall(fullpath)
                f=os.removedirs
                self.rmgeneric(fullpath, f)
                
                
    ERROR_STR= """Error removing %(path)s, %(error)s """

    def rmgeneric(self, path, __func__):
    
        try:
            __func__(path)
            print 'Removed ', path
        except OSError, (errno, strerror):
            self.onerror(__func__, path)

    def onerror(self, func, path):

        sys.exc_clear()
        
        import stat
        if not os.access(path, os.W_OK):
            if os.path.exists(path):
                # Is the error an access error ?
                os.chmod(path, stat.S_IWUSR)
                func(path)
        else:
            print self.ERROR_STR % {'path' : path, 'error': strerror }
            
rf = clean_folders()
rf.do_it()
