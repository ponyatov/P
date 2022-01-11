# \ import
import os, sys, time, re
import datetime as dt
import inspect
# / import

# \ core

class Object:

    ## @name constructor

    ## constructor
    def __init__(self, V):
        ## scalar: object name, string/number value,..
        self.value = V
        ## associative array = env/namespace = AST attributes
        self.slot = {}
        ## ordered container = vector = stack = AST subtree
        self.nest = []

    ## Python's types boxing
    def box(self, that):
        if isinstance(that, Object): return that
        if isinstance(that, str): return S(that)
        raise TypeError(['box', type(that), that])

    ## @name text dump/repr

    ## `print` callback
    def __repr__(self):
        return self.dump()

    ## full text tree dump
    def dump(self, cycle=[], depth=0, prefix='', test=False):
        # head
        def pad(depth): return '\n' + '\t' * depth
        ret = pad(depth) + self.head(prefix, test)
        # cycle
        if not depth: cycle = []
        if self in cycle: return f'{ret} _/'
        else: cycle.append(self)
        # slot{}s
        for i in self.keys():
            ret += self[i].dump(cycle, depth + 1, f'{i} = ', test)
        # nest[]ed
        for j, k in enumerate(self):
            ret += k.dump(cycle, depth + 1, f'{j}: ', test)
        # subtree
        return ret

    ## `<T:V>` single-line header
    def head(self, prefix='', test=False):
        gid = f' @{id(self):x}' if not test else ''
        return f'{prefix}<{self.tag()}:{self.val()}>{gid}'

    ## `<T:` object type/class tag
    def tag(self):
        return self.__class__.__name__.lower()

    ## `:V>` stringified object value
    def val(self):
        return f'{self.value}'

    ## f-string callback
    def __format__(self, spec):
        ret = self.val()
        if 'u' in spec: ret = ret.upper()
        return ret

    ## @name operator

    def keys(self): return sorted(self.slot.keys())

    def __iter__(self): return iter(self.nest)

    ## `A // B ~> A.push(B)`
    def __floordiv__(self, that):
        self.nest.append(self.box(that)); return self

    ## `A[key]`
    def __getitem__(self, key):
        if isinstance(key, int): return self.nest[key]
        raise TypeError(['__getitem__', type(key), key])

    ## @name stack operation

    def dropall(self): self.nest = []; return self


class Primitive(Object): pass

## nested string (source code)
class S(Primitive):
    def __init__(self, start=None, end=None, pfx=None, sfx=None):
        super().__init__(start)
        self.start = start; self.end = end
        self.pfx = pfx; self.sfx = sfx

    def gen(self, depth=0, to=None):
        ret = ''
        if self.pfx is not None:
            ret += f'{to.tab*depth}{self.pfx}\n' if self.pfx else '\n'
        if self.start is not None:
            ret += f'{to.tab*depth}{self.start}\n'
        for i in self:
            ret += i.gen(depth + 1, to)
        if self.end is not None:
            ret += f'{to.tab*depth}{self.end}\n'
        return ret

## code section
class Sec(S):
    def gen(self, depth=0, to=None):
        ret = ''
        if self.nest:
            if self.pfx is not None:
                ret += f'{to.tab*depth}{self.pfx}\n' if self.pfx else '\n'
            if self.start is not None:
                ret += f'{to.tab*depth}{to.comment} \\ {self.start}\n'
            for i in self:
                ret += i.gen(depth + 0, to)
            if self.end is not None:
                ret += f'{to.tab*depth}{to.comment} / {self.end}\n'
            else:
                if self.start is not None:
                    ret += f'{to.tab*depth}{to.comment} / {self.start}\n'
        return ret

class Container(Object): pass
class Vector(Container): pass
class Stack(Container): pass
class Queue(Container): pass
class Map(Container): pass

class IO(Object):
    def __init__(self, V):
        super().__init__(V)
        self.path = V

class Dir(IO):
    def __init__(self, V):
        super().__init__(V)
        self.giti = gitiFile()

    def sync(self):
        self // self.giti
        try: os.mkdir(self.path)
        except FileExistsError: pass
        for i in self: i.sync()

    def __floordiv__(self, that):
        assert isinstance(that, IO)
        that.path = f'{self.path}/{that.path}'
        return super().__floordiv__(that)

class File(IO):
    def __init__(self, V, ext='', tab=' ' * 4, comment='#'):
        super().__init__(V + ext)
        self.ext = ext; self.tab = tab; self.comment = comment
        self.top = Sec(); self.bot = Sec()

    def sync(self):
        with open(self.path, 'w') as F:
            F.write(self.top.gen(to=self))
            for i in self: F.write(i.gen(to=self))
            F.write(self.bot.gen(to=self))

    def __floordiv__(self, that):
        return super().__floordiv__(that)


class mdFile(File):
    def __init__(self, V='README', ext='.md'):
        super().__init__(V, ext)

    def sync(self):
        self.dropall() \
            // f'#  {self.p}' \
            // f'## {self.p.TITLE}' \
            // f'{self.p.ABOUT}' \
            // f'\n{self.p.CopyRight()}' \
            // f'\ngithub: {self.p.GITHUB}'
        self \
            // (S('```', '```', pfx='\n## Install\n')
                // f'$ git clone -o bb git@bitbucket.org:ponyatov/{self.p}.git ~/{self.p}'
                // f'$ cd ~/{self.p} ; make install'
                )
        super().sync()

class mkFile(File):
    def __init__(self, V='Makefile', ext='', tab='\t'):
        super().__init__(V, ext, tab=tab)

class pyFile(File):
    def __init__(self, V, ext='.py'):
        super().__init__(V, ext)

    def genClass(self, depth=0, cls=None):
        sup = '(%s)' % ','.join(
            map(lambda i: i.__name__, cls.sup)) if cls.sup else ''
        pss = '\n' if cls.nest else ' pass\n'
        ret = f'\nclass {cls}{sup}:{pss}'
        return ret

    def genFn(self, depth=0, fn=None):
        ret = ''
        if fn.pfx is not None:
            ret += f'{self.tab*depth}{self.comment*2} {fn.pfx}\n' if fn.pfx else '\n'
        if fn.descr:
            ret += f'{self.tab*depth}{self.comment*2} {fn.descr}\n'
        args = ', '.join(fn.args)
        ret += f'{self.tab*depth}def {fn}({args}):\n'
        for i in fn: ret += i.gen(depth + 1, self)
        return ret

class watFile(File):
    def __init__(self, V, ext='.wat', comment=';;'):
        super().__init__(V, ext, comment=comment)
        self.top // f'{self.comment} {self.head(test=True)}' // ''
        self // Module(V)

    def genModule(self, depth=0, mod=None):
        return S(f'(module', ')').gen(depth, self)

class cppFile(File):
    def __init__(self, V, ext='.cpp', comment='//'):
        super().__init__(V, ext, comment=comment)

    def genClass(self, depth=0, cls=None):
        ret = S(f'class {cls} {{', '};', pfx='')
        ret // Fn('Object', ['const char* V'], '')
        for i in cls: ret // i
        return ret.gen(depth, self)

    def genFn(self, depth=0, fn=None):
        ret = Sec(pfx='')
        if fn.pfx is not None:
            ret // f'{self.tab*depth}{self.comment*2} {fn.pfx}\n' if fn.pfx else '\n'
        if fn.descr:
            ret // f'{self.tab*depth}{self.comment*2} {fn.descr}\n'
        #
        args = ', '.join(fn.args)
        #
        if fn.ret == '': retype = ''
        elif fn.ret is None: retype = 'void '
        else: retype = fn.ret
        #
        ret.func = S(f'{retype}{fn}({args}) {{', '}')
        ret // ret.func
        for i in fn: ret.func // i
        return ret.gen(depth, self)

class hppFile(cppFile):
    def __init__(self, V, ext='.hpp'):
        super().__init__(V, ext)

    def genClass(self, depth=0, cls=None):
        ret = S(f'class {cls} {{', '};', pfx='')
        for f in cls.fields:
            ret // f.gen(depth + 1, self)
        for i in cls: ret // i
        return ret.gen(depth, self)

    def genFn(self, depth=0, fn=None):
        ret = Sec()
        #
        args = ', '.join(fn.args)
        #
        if fn.ret == '': retype = ''
        elif fn.ret is None: retype = 'void '
        else: retype = f'{fn.ret} '
        #
        ret.func = S(f'{retype}{fn}({args});')
        ret // ret.func
        return ret.gen(depth, self)

class gitiFile(File):
    def __init__(self, V='', ext='.gitignore'):
        super().__init__(V, ext)
        self.bot // '!.gitignore'


class jsonFile(File):
    def __init__(self, V, ext='.json', comment='//'):
        super().__init__(V, ext, comment=comment)


class Active(Object): pass

class Fn(Active):
    def __init__(self, V, args=[], ret=None, pfx=None, descr=None):
        if callable(V):
            sig = inspect.signature(V).parameters
            # print(inspect.getsource(V))
            args = map(lambda i: f'{sig[i]}', sig)
            V = V.__name__
        super().__init__(V)
        self.ret = ret
        self.args = args
        self.pfx = pfx
        self.descr = descr

    def gen(self, depth=0, to=None):
        return to.genFn(depth, self)

class Meta(Object): pass

class Module(Meta):
    def gen(self, depth=0, to=None):
        return to.genModule(depth, self)

class Class(Meta):
    def __init__(self, C, sup=[]):
        assert callable(C)
        self.C = C; self.sup = sup
        super().__init__(C.__name__)
        self.fields = Vector('fields')
        self.public = S('public:'); self // self.public
        self.public // Fn(f'{self}', ['const char* V'], '')

    def gen(self, depth=0, to=None):
        return to.genClass(depth, self)

class Field(Meta):
    def __init__(self, typ, V):
        super().__init__(V)
        self.typ = typ

    def gen(self, depth=0, to=None):
        return f'{to.tab*depth}{self.typ} {self.value};'

class Meth(Fn):
    def __init__(self, V, args=[], pfx=None, descr=None):
        super().__init__(V, ['self'] + args, pfx=pfx, descr=descr)

class Project(Meta):
    def __init__(self, V=None):
        if not V: V = os.getcwd().split('/')[-1]
        super().__init__(V)
        self.metainfo()
        self.d = Dir(f'{self}')
        self.readme()
        self.mk()
        self.giti()
        self.dirs()
        self.vscode()
        self.apt()
        self.reqs()
        self.py()
        self.cpp()
        self.wasm()

    def cpp(self):
        self.ext // '"ms-vscode.cpptools",'
        self.cpp_mk()
        self.cpp_c()
        self.cpp_h()

    def cpp_mk(self):
        self.mk.src // f'C += src/$(MODULE).cpp' // f'H += src/$(MODULE).hpp'
        self.mk.src // f'S += $(C) $(H)'
        self.mk.cfg // 'CFLAGS += -pipe -O0 -g2 -Isrc -Itmp'
        self.mk.all // (S('cpp: bin/$(MODULE)', pfx='') // '$^ $@')
        self.mk.rule // (S('bin/$(MODULE): $(C) $(H)')
                         // '$(CXX) $(CFLAGS) -o $@ $(C) $(L) && size $@')

    def cpp_c(self):
        self.cpp = cppFile(f'{self}'); self.src // self.cpp
        self.cpp.top \
            // f'#include <{self}.hpp>'
        self.cpp \
            // (Fn('main', ['int argc', 'char *argv[]'], ret='int')
                // 'cout << (new Object("Hello"))->dump() << endl;'
                // 'return 0;')

    def cpp_h(self):
        self.hpp = hppFile(f'{self}'); self.src // self.hpp
        #
        H = f'{self:u}_H'
        self.hpp.top \
            // f'#ifndef {H}' // f'#define {H}'
        self.hpp.bot // f'#endif // {H}'
        #
        self.hpp.include = Sec(pfx=''); self.hpp // self.hpp.include
        for i in ['iostream', 'sstream', 'locale', 'stdlib.h', 'stdio.h', 'assert.h']:
            self.hpp.include // f'#include <{i}>'
        self.hpp.include // 'using namespace std;'
        #
        self.hpp.qt = Sec(pfx=''); self.hpp.include // self.hpp.qt
        for j in ['QApplication', 'QString']:
            self.hpp.qt // f'#include <{j}>'
        #
        self.hpp.metal = Sec('metal', pfx=''); self.hpp // self.hpp.metal
        self.hpp.object = Class(Object)
        self.hpp.object.fields // Field('QString', 'value')
        self.hpp.metal // self.hpp.object
        self.hpp.object.public \
            // Fn('dump', ['int depth=0', 'QString prefix=""'], 'QString')

    def dirs(self):
        #
        self.bin = Dir('bin'); self.d // self.bin
        self.bin.giti.top // '*'
        #
        self.doc = Dir('doc'); self.d // self.doc
        self.doc.giti.top // '*.pdf' // '*.djvu'
        #
        self.lib = Dir('lib'); self.d // self.lib
        #
        self.src = Dir('src'); self.d // self.src
        #
        self.tmp = Dir('tmp'); self.d // self.tmp
        self.tmp.giti.top // '*'

    def vscode(self):
        self.vscode = Dir('.vscode'); self.d // self.vscode
        self.settings()
        self.tasks()
        self.extensions()

    def settings(self):
        self.settings = (jsonFile('settings') // (S('{', '}')))
        self.vscode // self.settings
        #

        def multi(key, cmd):
            return (S('{', '},')
                    // f'"command": "multiCommand.{key}",'
                    // (S('"sequence": [', ']')
                    // '"workbench.action.files.saveAll",'
                    // (S('{"command": "workbench.action.terminal.sendSequence",')
                        // f'"args": {{"text": "\\n{cmd}\\n"}}}}')))
        self.settings.multi = (Sec('multi')
                               // (S('"multiCommand.commands": [', '],')
                                   // multi('f11', 'clear; make meta')
                                   // multi('f12', 'clear; make cpp')
                                   )
                               )
        self.settings[0] // self.settings.multi
        #
        self.settings.files = Sec('files', pfx='')
        self.settings[0] // self.settings.files
        #

        def files(start, end): return (S(start, end)
                                       // f'"**/{self}/":true, "**/docs/**":true,'
                                       )
        #
        self.settings.exclude = (files('"files.exclude": {', '},'))
        self.settings.files // self.settings.exclude
        #
        self.settings.watcher = (files('"files.watcherExclude": {', '},'))
        self.settings.files // self.settings.watcher
        #
        self.settings.assoc = (S('"files.associations": {', '},'))
        self.settings.files // self.settings.assoc
        #
        self.settings.editor = (Sec('editor', pfx='')
                                // '"editor.tabSize": 4,'
                                // '"editor.rulers": [80],'
                                // '"workbench.tree.indent": 32,'
                                )
        self.settings[0] // self.settings.editor

    def tasks(self):
        self.tasks = jsonFile('tasks'); self.vscode // self.tasks
        task = S('"tasks": [', ']')
        self.tasks // (S('{', '}')
                       // '"version": "2.0.0",' // task)

        def t(make='make', cmd=None):
            return (S('{', '},')
                    // f'"label":          "project: {cmd}",'
                    // f'"type":           "shell",'
                    // f'"command":        "{make} {cmd}",'
                    // f'"problemMatcher": []')
        for cmd in ['install', 'update', 'dev', 'shadow']:
            task // t(cmd=cmd)

    def wasm(self):
        self.ext // '"dtsvet.vscode-wasm",'
        self.dev // 'wabt npm'
        #
        self.mk.tool // 'WAT     = wat2wasm'
        self.mk.src // 'W += src/hello.wat' // 'S += $(W)'
        #
        self.wasm = watFile('hello'); self.src // self.wasm
        self.wlib = watFile('lib'); self.src // self.wlib

    def extensions(self):
        self.ext = S('"recommendations": [', ']')
        self.extensions = (jsonFile('extensions') // (S('{', '}') // self.ext))
        (self.ext
            // '"ryuta46.multi-command",'
            // '"stkb.rewrap",'
            // '"tabnine.tabnine-vscode",'
            // '// "auchenberg.vscode-browser-preview",'
            // '// "ms-azuretools.vscode-docker",'
            // '"tht13.python",')
        self.vscode // self.extensions

    def apt(self):
        self.apt = File('apt', '.txt'); self.d // self.apt
        self.apt // 'git make curl' // 'python3 python3-venv'
        #
        self.dev = File('apt', '.dev'); self.d // self.dev
        self.dev \
            // 'code meld doxygen' \
            // 'build-essential flex bison' \
            // 'qtbase5-dev'

    def reqs(self):
        self.reqs = File('requirements', '.txt'); self.d // self.reqs

    def mk(self):
        self.mk = mkFile(); self.d // self.mk
        #
        self.mk.var = (Sec('var')
                       // 'MODULE  = $(notdir $(CURDIR))'
                       // 'OS      = $(shell uname -s)'
                       // 'NOW     = $(shell date +%d%m%y)'
                       // 'REL     = $(shell git rev-parse --short=4 HEAD)'
                       // 'BRANCH  = $(shell git rev-parse --abbrev-ref HEAD)'
                       // 'CORES   = $(shell grep processor /proc/cpuinfo| wc -l)'
                       )
        self.mk // self.mk.var
        #
        self.mk.dir = (Sec('dir', pfx='')
                       // 'CWD = $(CURDIR)'
                       // 'BIN = $(CWD)/bin'
                       // 'DOC = $(CWD)/doc'
                       // 'LIB = $(CWD)/lib'
                       // 'SRC = $(CWD)/src'
                       // 'TMP = $(CWD)/tmp'
                       )
        self.mk // self.mk.dir
        #
        self.mk.tool = (Sec('tool', pfx='')
                        // 'CURL    = curl -L -o'
                        // 'PY      = $(shell which python3)'
                        // 'PIP     = $(shell which pip3)'
                        // 'PEP     = $(shell which autopep8)'
                        // 'PYT     = $(shell which pytest)'
                        )
        self.mk // self.mk.tool
        #
        self.mk.cfg = Sec('cfg', pfx='')
        self.mk // self.mk.cfg
        #
        self.mk.src = (Sec('src', pfx='')
                       // 'Y += $(MODULE).py' // 'S += $(Y)'
                       )
        self.mk // self.mk.src
        #
        self.mk.bin = (Sec('bin', pfx=''))
        self.mk // self.mk.bin
        #
        self.mk.all = (Sec('all', pfx='')
                       // (S('meta: $(PY) $(Y)') // '$^ $@' // '$(MAKE) tmp/format_py')
                       )
        self.mk // self.mk.all
        #
        self.mk.all \
            // (S('tmp/format_py: $(Y)', pfx='\nformat: tmp/format_py')
                // '$(PEP) --ignore=E26,E302,E305,E401,E402,E701,E702 --in-place $?'
                // 'touch $@')
        #
        self.mk.rule = Sec('rule', pfx='')
        self.mk // self.mk.rule
        #
        self.mk.doc = Sec('doc', pfx='')
        self.mk // self.mk.doc
        #
        self.mk.install = Sec('install', pfx='')
        self.mk // self.mk.install
        #
        self.mk.install // (S('install: $(OS)_install'))
        #
        self.mk.install // (S('update: $(OS)_update'))
        #
        self.mk.install // (S('Linux_install Linux_update:')
                            // 'sudo apt update'
                            // 'sudo apt install -u `cat apt.dev apt.txt`')
        #
        self.mk.merge = (Sec('merge', pfx='')
                         // 'SHADOW ?= shadow'
                         // 'MERGE  += README.md Makefile apt.txt apt.dev $(S)'
                         // 'MERGE  += bin doc lib src tmp .gitignore'
                         // 'MERGE  += requirements.txt'
                         )
        self.mk // self.mk.merge

    def py(self):
        self.py = pyFile(f'{self}'); self.d // self.py
        self.py // (Sec('import')
                    // 'import os, sys, time, re'
                    // 'import datetime as dt'
                    // 'import inspect'
                    )
        #
        self.py.object = Class(Object)
        #
        self.py.object.constructor = Sec() // S('## @name constructor\n', pfx='')
        self.py.object // self.py.object.constructor
        self.py.object.constructor \
            // Meth('__init__', ['V'], descr='constructor')
        self.py.object.constructor \
            // Meth('box', ['that'], descr='Python\'s types boxing', pfx='')
        #
        self.py.object.dump = Sec() // S('## @name text dump/repr\n', pfx='')
        self.py.object // self.py.object.dump
        self.py.object.dump \
            // Meth('__repr__', descr='`print` callback')
        self.py.object.dump \
            // (Meth(Object.dump, descr='full text tree dump', pfx='')
                // "# head"
                // "# cycle"
                // "# slot{}s"
                // "# nest[]ed"
                // "# subtree"
                )
        self.py.object.dump \
            // Meth(Object.head, descr='`<T:V>` single-line header', pfx='')
        self.py.object.dump \
            // (Meth(Object.tag, descr='`<T:` object type/class tag', pfx='')
                // "return self.__class__.__name__.lower()")
        self.py.object.dump \
            // (Meth(Object.val, descr='`:V>` stringified object value', pfx='')
                // "return f'{self.value}'")
        self.py.object.dump \
            // Meth(Object.__format__, descr='f-string callback', pfx='')
        #
        self.py // (Sec('core', pfx='')
                    // self.py.object
                    // Class(Primitive, [Object])
                    // Class(S, [Primitive])
                    // Class(Sec, [S])
                    // Class(IO, [Object])
                    // Class(Dir, [IO])
                    // Class(File, [IO])
                    // Class(mdFile, [File])
                    // Class(mkFile, [File])
                    // Class(pyFile, [File])
                    // Class(gitiFile, [File])
                    )

    def metainfo(self):
        self.TITLE = f'{self}'
        self.ABOUT = ''
        self.AUTHOR = 'Dmitry Ponyatov'
        self.EMAIL = 'dponyatov@gmail.com'
        self.YEAR = '2021'
        self.LICENSE = 'All rights reserved'
        self.GITHUB = f'https://bitbucket.org/ponyatov/{self}/src/shadow/'

    def readme(self):
        self.readme = mdFile('README'); self.d // self.readme
        self.readme.p = self

    def giti(self):
        self.d.giti.top // '*~' // '*.swp' // '*.log' // ''
        self.d.giti // f'/{self}/' // '/docs/' // ''

    def sync(self):
        self.d.sync()

    def CopyRight(self):
        return f'(c) {self.AUTHOR} <{self.EMAIL}> {self.YEAR} {self.LICENSE}'

# / core

if __name__ == '__main__':
    if sys.argv[1] == 'meta':
        p = Project()
        p.TITLE = 'meta/prototype'
        p.ABOUT = '''
* metaL/Python powered code generation
* WASM target'''
        p.sync()
    else:
        raise SyntaxError(sys.argv)
