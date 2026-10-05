.PHONY: check test catalog install uninstall render release
check:
	python3 scripts/validate.py
	python3 -m unittest discover -s tests -v
	./install.sh render --check

test:
	python3 -m unittest discover -s tests -v

catalog:
	python3 scripts/catalog.py

render:
	./install.sh render

install:
	./install.sh

uninstall:
	./install.sh uninstall

release:
	python3 scripts/package.py --version "$$(cat VERSION)"
