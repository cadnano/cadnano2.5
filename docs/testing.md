# Testing

Cadnano has a handful of automated tests that get run automatically by
[TravisCI](https://travis-ci.org/cadnano/cadnano2.5) on every commit pushed to
Github. The tests help ensure the integrity of the our data model, or at least
notify us quickly when we've broken something. We also test the GUI by recording
and playing back user interactions with
[QTest](http://doc.qt.io/qt-5/qtest-overview.html).

If you'd like to modify cadnano, we recommend setting up automated testing in
your local development environment. You'll first want to install
[pytest](https://docs.pytest.org/).

```
pip install pytest
```


## Running Tests

To run non-GUI tests:

```
pytest cadnano/tests
```

To run GUI tests:

```
pytest -c cadnano/tests/pytestgui.ini cadnano/tests/
```

Currently, we do not automate GUI tests on TravisCI, so they must be run locally.


## Automating Tests with a Pre-Commit Hook

Pre-commit hooks are a great way to make sure that the test suite is run before
committing. Doing this ensures that code that is committed will always pass
the test suite.

A script to accomplish this when committing via the `git` command line is
included in this repository.  To activate it, run

```
ln -s "$(git rev-parse --show-toplevel)/misc/git-hooks/pre-commit" $(git rev-parse --show-toplevel)/.git/hooks/
```

anywhere in the cadnano repository.  This will symlink the pre-commit hook to
your `.git/hooks` directory.  Now, whenever you commit, the test suite will be
run before you commit:

```
❱ git commit
Running tests in $HOME/cadnano2.5/cadnano/tests...

============================== test session starts ==============================
platform darwin -- Python 3.6.3, pytest-3.3.1, py-1.5.2, pluggy-0.6.0
PyQt5 5.9.2 -- Qt runtime 5.9.3 -- Qt compiled 5.9.3
rootdir: $HOME/cadnano2.5/cadnano/tests, inifile: pytest.ini
plugins: qt-2.3.0
collected 12 items

cadnano/tests/functionaltest.py .......                                    [ 58%]
cadnano/tests/nucleicacidparttest.py ....                                  [ 91%]
cadnano/tests/strandsettest.py .                                           [100%]

=========================== 12 passed in 1.47 seconds ===========================
```

and if any of the tests fail, committing will be blocked:

```
Running tests in $HOME/cadnano2.5/cadnano/tests...

============================== test session starts ==============================
platform darwin -- Python 3.6.3, pytest-3.3.1, py-1.5.2, pluggy-0.6.0
PyQt5 5.9.2 -- Qt runtime 5.9.3 -- Qt compiled 5.9.3
rootdir: $HOME/cadnano2.5/cadnano/tests, inifile: pytest.ini
plugins: qt-2.3.0
collected 5 items / 1 errors

==================================== ERRORS =====================================
______________________ ERROR collecting functionaltest.py _______________________
cadnano-virtualenv/lib/python3.6/site-packages/_pytest/python.py:403: in _importtestmodule
    mod = self.fspath.pyimport(ensuresyspath=importmode)
cadnano-virtualenv/lib/python3.6/site-packages/py/_path/local.py:668: in pyimport
    __import__(modname)
E     File "$HOME/cadnano2.5/cadnano/tests/functionaltest.py", line 14
E       def
E         ^
E   SyntaxError: invalid syntax
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 errors during collection !!!!!!!!!!!!!!!!!!!!
============================ 1 error in 0.68 seconds ============================

Tests failed; commit aborted
To commit without this hook running, pass the --no-verify argument
```

As the last line says, if you want to ignore the fact that tests are failing and
commit anyway, pass the `--no-verify` argument to `git commit`.
