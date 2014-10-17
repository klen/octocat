VENV=$(shell echo "$${VDIR:-'.env'}")
MODULE=octocat

all: $(VENV)

.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile

.PHONY: clean
# target: clean - Clean repo
clean:
	@rm -rf build dist docs/_build
	find $(CURDIR)/$(MODULE) -name "*.pyc" -delete
	find $(CURDIR)/$(MODULE) -name "*.orig" -delete
	find $(CURDIR)/$(MODULE) -name "__pycache__" -delete


# ==============
#  Bump version
# ==============

.PHONY: release
VERSION?=minor
# target: release - Bump version
release:
	@pip install bumpversion
	@bumpversion $(VERSION)
	@git checkout master
	@git merge develop
	@git checkout develop
	@git push --all
	@git push --tags

.PHONY: minor
minor: release

.PHONY: patch
patch:
	make release VERSION=patch


# ===============
#  Build package
# ===============

.PHONY: register
# target: register - Register module on PyPi
register:
	@python setup.py register

.PHONY: upload
# target: upload - Upload module on PyPi
upload: clean docs
	@$(VENV)/bin/pip install twine wheel
	@python setup.py sdist bdist_wheel
	@twine upload dist/*

.PHONY: docs
# target: docs - Compile the docs
docs: docs
	@$(VENV)/bin/pip install sphinx
	python setup.py build_sphinx --source-dir=docs/ --build-dir=docs/_build --all-files
	# python setup.py upload_sphinx --upload-dir=docs/_build/html


# =============
#  Development
# =============

$(VENV): requirements.txt
	@[ -d $(VENV) ] || virtualenv --no-site-packages $(VENV)
	@$(VENV)/bin/pip install -r requirements.txt

.PHONY: t
# target: t - Runs tests
t: clean $(VENV)
	$(VENV)/bin/pip install -r requirements-tests.txt
	$(VENV)/bin/py.test $(TEST) -s

.PHONY: audit
# target: audit - Audit code
audit:
	@pylama $(MODULE) -i E501

.PHONY: serve
# target: serve - Run HTTP server with compiled docs
serve:
	pyserve docs/_build/html/

.PHONY: pep8
pep8:
	find $(MODULE) -name "*.py" | xargs -n 1 autopep8 -i
