EXTRA_DIST= \
 m4 \
 AUTHORS \
 COPYING \
 autogen.sh \
 setup.py.in \
 letce2 \
 scripts \
 $(PACKAGE).spec.in

BUILT_SOURCES = \
 setup.py                        

all-local:
	$(PYTHON) setup.py build_ext --inplace
	$(PYTHON) setup.py build

clean-local: setup.py
	$(PYTHON) setup.py clean
	-rm -rf build
	-rm -rf dist
	-rm -f $(BUILT_SOURCES)
	-rm -f $(PACKAGE)-*.tar.gz
	-find . -name "*.pyc" -delete
	-rm -f .installedfiles
	-rm -rf .rpmbuild
	-rm -f $(PACKAGE).spec

DISTCLEANFILES=setup.py

sdist:
	$(PYTHON) setup.py sdist

edit = sed \
        -e 's|@VERSION[@]|$(VERSION)|g'

setup.py:	setup.py.in
	if test -f $@; then chmod u+w $@; fi
	$(edit) $< > $@
	chmod g-w,u-w $@

install-exec-hook: $(BUILT_SOURCES)
	$(PYTHON) setup.py install \
	    -O1 \
        --record .installedfiles \
	    --prefix=$(prefix) \
	    --exec-prefix=$(exec_prefix) \
	    $(if $(DESTDIR),--root=$(DESTDIR))

uninstall-hook:
	if test -f .installedfiles; then xargs -a .installedfiles rm -f; fi

RPMARCH=`arch`

if HAVE_RPMBUILD

rpm: $(PACKAGE).spec dist-gzip
	mkdir -p .rpmbuild/BUILD \
	.rpmbuild/SPECS \
	.rpmbuild/SOURCES \
	.rpmbuild/SRPMS \
	.rpmbuild/RPMS/noarch \
	.rpmbuild/tmp
	cp -f $(PACKAGE)-$(VERSION).tar.gz .rpmbuild/SOURCES
	rpmbuild --clean -ba $(top_srcdir)/$(PACKAGE).spec --target $(RPMARCH) \
    --define "_topdir $$PWD/.rpmbuild" \
    --define "_tmppath $$PWD/.rpmbuild/tmp"
	@echo "============================================================"
	@echo "RPMs located in .rpmbuild/RPMS and .rpmbuild/SRPMS"

endif

$(PACKAGE).spec: $(PACKAGE).spec.in
	if test -f $@; then chmod u+w $@; fi
	$(edit) $< > $@
	chmod g-w,u-w $@
