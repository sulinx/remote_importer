import zipfile,StringIO, imp, sys, os.path,os,logging,types,urllib2


# Order in which we probe the zipfile directory.
# This is a list of (suffix, is_package) tuples.
_SEARCH_ORDER = [
    # Try .py first since that is most common.
    ('.py', False),
    ('/__init__.py', True),
]


# Cache for opened zipfiles.
# Maps zipfile pathnames to zipfile.ZipFile instances.
_zipfile_cache = {}

class ZipImportError(ImportError):
    """Exception raised by zipimporter objects."""

class zipimporter:


  def __init__(self,zipfilename, fileobj):

    self.zipfile = fileobj


  def __repr__(self):

    name = self.zipfilename
    if self.prefix:
      name = os.path.join(name, self.prefix)
    return '<zipimporter object %s>' % name

  def _get_info(self, fullmodname):

    parts = fullmodname.split('.')
    submodname = parts[-1]
    modpath = '/'.join(parts)
    for suffix, is_package in _SEARCH_ORDER:
      relpath = modpath + suffix
      try:
        self.zipfile.getinfo(relpath)
      except KeyError:
        pass
      else:
        return submodname, is_package, relpath
    msg = ('Can\'t find module %s in zipfile %s with prefix %r' %
           (fullmodname, self.zipfilename, self.prefix))
    ##logging.debug(msg)
    raise ZipImportError(msg)

  def _get_source(self, fullmodname):

    submodname, is_package, relpath = self._get_info(fullmodname)
    fullpath = '%s/%s' % (self.zipfilename, relpath)
    source = self.zipfile.read(relpath)
    source = source.replace('\r\n', '\n')
    source = source.replace('\r', '\n')
    return submodname, is_package, fullpath, source

  def find_module(self, fullmodname, path=None):

    try:
      submodname, is_package, relpath = self._get_info(fullmodname)
    except ImportError:
      ##logging.debug('find_module(%r) -> None', fullmodname)
      return None
    else:
      ##logging.debug('find_module(%r) -> self', fullmodname)
      return self

  def load_module(self, fullmodname):

    ##logging.debug('load_module(%r)', fullmodname)
    submodname, is_package, fullpath, source = self._get_source(fullmodname)
    code = compile(source, fullpath, 'exec')
    mod = sys.modules.get(fullmodname)
    if mod is None:
      mod = sys.modules[fullmodname] = types.ModuleType(fullmodname)
    mod.__loader__ = self
    mod.__file__ = fullpath
    mod.__name__ = fullmodname
    if is_package:
      mod.__path__ = [os.path.dirname(mod.__file__)]
    exec code in mod.__dict__
    return mod

  # Optional PEP 302 functionality.  See the PEP for specs.

  def get_data(self, fullpath):

    required_prefix = os.path.join(self.zipfilename, '')
    if not fullpath.startswith(required_prefix):
      raise IOError('Path %r doesn\'t start with zipfile name %r' %
                    (fullpath, required_prefix))
    relpath = fullpath[len(required_prefix):]
    try:
      return self.zipfile.read(relpath)
    except KeyError:
      raise IOError('Path %r not found in zipfile %r' %
                    (relpath, self.zipfilename))

  def is_package(self, fullmodname):
    """Return whether a module is a package."""
    submodname, is_package, relpath = self._get_info(fullmodname)
    return is_package

  def get_code(self, fullmodname):
    """Return bytecode for a module."""
    submodname, is_package, fullpath, source = self._get_source(fullmodname)
    return compile(source, fullpath, 'exec')

  def get_source(self, fullmodname):
    """Return source code for a module."""
    submodname, is_package, fullpath, source = self._get_source(fullmodname)
    return source

def remote_import(packagename, url):
    import sys, urllib2
    zipfile = urllib2.urlopen(url).read()
    zipimporter('packagename',zipfile)
