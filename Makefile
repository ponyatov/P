# \ var
MODULE  = $(notdir $(CURDIR))
OS      = $(shell uname -s)
NOW     = $(shell date +%d%m%y)
REL     = $(shell git rev-parse --short=4 HEAD)
BRANCH  = $(shell git rev-parse --abbrev-ref HEAD)
CORES   = $(shell grep processor /proc/cpuinfo| wc -l)
# / var

# \ dir
CWD = $(CURDIR)
BIN = $(CWD)/bin
DOC = $(CWD)/doc
LIB = $(CWD)/lib
SRC = $(CWD)/src
TMP = $(CWD)/tmp
# / dir

# \ tool
CURL    = curl -L -o
PY      = $(shell which python3)
PIP     = $(shell which pip3)
PEP     = $(shell which autopep8)
PYT     = $(shell which pytest)
QMAKE   = qmake -qt=5
QTQUERY = $(QMAKE) -query
NPM     = npm
NODE    = node
WAS     = wat2wasm
WDIS    = wasm2wat
WAL     = wasm-validate
WAI     = wasm-interp
# / tool

# \ cfg
CFLAGS += -pipe -O0 -g2 -Isrc -Itmp
CFLAGS += -I$(shell $(QTQUERY) QT_INSTALL_HEADERS)
# / cfg

# \ src
Y += $(MODULE).py
S += $(Y)
C += src/$(MODULE).cpp
H += src/$(MODULE).hpp
S += $(C) $(H)
W += src/hello.wat src/lib.wat
S += $(W)
# / src

# \ bin
WASM = node/hello.wasm node/lib.wasm
# / bin

# \ all
meta: $(PY) $(Y)
	$^ $@
	$(MAKE) tmp/format_py

format: tmp/format_py
tmp/format_py: $(Y)
	$(PEP) --ignore=E26,E302,E305,E401,E402,E701,E702 --in-place $?
	touch $@

cpp: bin/$(MODULE)
	$^ $@

wasm: $(WASM)
	$(WAI) $<
# / all

# \ rule
bin/$(MODULE): $(C) $(H)
	$(CXX) $(CFLAGS) -o $@ $(C) $(L) && size $@
node/%.wasm: src/%.wat Makefile
	$(WAS) -o $@ $< && $(WAL) $@ && hexdump -C $@
	$(WDIS) -o $(shell echo $@.wat|sed 's/node/tmp/') $@
# / rule

# \ install
install: $(OS)_install
update: $(OS)_update
Linux_install Linux_update:
	sudo apt update
	sudo apt install -u `cat apt.dev apt.txt`
# / install

# \ merge
SHADOW ?= shadow
MERGE  += README.md Makefile apt.txt apt.dev $(S)
MERGE  += bin doc lib src tmp .gitignore
MERGE  += requirements.txt
# / merge
