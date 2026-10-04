.PHONY: check test catalog install uninstall release
check:
	python3 scripts/validate.py
	python3 -m unittest discover -s tests -v
	sh -n install.sh uninstall.sh update.sh

test:
	python3 -m unittest discover -s tests -v

catalog:
	python3 scripts/catalog.py

install:
	./install.sh

uninstall:
	./uninstall.sh

release:
	python3 scripts/package.py --version "$$(cat VERSION)"
