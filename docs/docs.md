
# Docs

Cadnano2.5 documentation is built with [sphinx] and hosted at [readthedocs.io].

## Building the docs

**Summary**

```
pip3 install sphinx sphinx_rtd_theme==0.2.5b2 recommonmark sphinx-autobuild
cd cadnano/docs
make clean
make api
make html
make livehtml
```

**Getting started**

Try setting up your own separate test [sphinx] project using `sphinx-quickstart`. Once you understand how sphinx works, read through the cadnano/docs [Makefile] and [conf.py] to understand our configuration.

**Install dependencies**

From the terminal, use pip to install sphinx and cadnano docs dependencies.

```
pip3 install sphinx sphinx_rtd_theme==0.2.5b2 recommonmark sphinx-autobuild
```

**Building**

First, make sure you are in the docs directory. Clear out the old documentation, if any.

```
cd cadnano/docs
make clean
```

Build the API. This generates sphinx .rst sources in docs/api using [sphinx-autodoc].


```
make api
```

Build the html. This converts the .rst and .md sources into HTML files. If successful, HTML pages should be placed in `_build/html`. You can open the index.html to inspect your edits.


```
make html
```

If you want to do everything together in a single command:

```
make clean; make api; make html
```


**Autobuild**

It can get tedious to rebuild the docs during heavy editing sessions. Instead, you can use [sphinx-autobuild] to rebuild the documentation whenever a change is detected. Autobuild conveniently spawns a local server (at 127.0.0.1:8000 unless you specify otherwise with `-p`) that will refresh as needed.

```
make livehtml
```

## reStructuredText vs Markdown

Like [docutils], Sphinx uses [reStructuredText], whose filenames have an `.rst` extension. ReStructuredText is tailored for technical documentation, and predates Markdown by about 2 years.

For the sake of consistency and leveraging core sphinx features, we initially just learned the basics of rST and used it for most doc sources, including the API. However, it is possible to create documentation in markdown format using [recommonmark]. This source files for this page ([cadnano/docs/docs.md]). New top-level documentation files that do not require rsT features should be created in markdown with the `.md` extension.


## Known Issues

**toctree Warnings**

When building the docs, you may see warnings like:

```
WARNING: toctree contains reference to nonexisting document 'api/cadnano.controllers.documentcontroller'
WARNING: toctree contains reference to nonexisting document 'api/cadnano.gui.mainwindow.ui_mainwindow'
WARNING: toctree contains reference to nonexisting document 'api/cadnano.views.documentwindow'
WARNING: toctree contains reference to nonexisting document 'api/cadnano.views.outlinerview.outlinertreewidget'
```

These modules import the PyQt5 classes in a way that doesn't play nicely with sphinx, so they are specifically excluded in `docs/conf.py`. Consequently, the documentation for these modules will be missing until someone tracks down the root cause of this issue and figures out a workaround. Possible starting point: [stackoverflow.com/questions/25960309/](http://stackoverflow.com/questions/25960309/)

**segfaults**

You may see segfaults when trying to run `make html` or `make livehtml` that
look like this:
```
...
reading sources... [ 70%] api/cadnano.views.pathview.strand.stranditem
reading sources... [ 71%] api/cadnano.views.pathview.strand.xoveritem
reading sources... [ 71%] api/cadnano.views.pathview.tools
reading sources... [ 72%] api/cadnano.views.pathview.tools.abstractpathtool
reading sources... [ 72%] api/cadnano.views.pathview.tools.addseqtool
make: *** [html] Segmentation fault: 11
```

If you encounter this, you may need to exclude the offending source from the
build.  Add the last source read before the segfault to the `exclude_patterns`
list in `conf.py`.  Ensure that you include the trailing `.rst` in the string.


## Contributing

We welcome docs-related pull requests, especially those that improve the docstring coverage of the API. Contributors will be credited on the [AUTHORS] page. If you are interested to help but not sure where to begin, please contact us!


[docutils]: http://docutils.sourceforge.net/
[sphinx]: http://www.sphinx-doc.org/
[readthedocs.io]: http://cadnano.readthedocs.io/
[AUTHORS]: https://github.com/cadnano/cadnano2.5/blob/master/AUTHORS
[sphinx-autodoc]: http://www.sphinx-doc.org/en/stable/man/sphinx-apidoc.html
[reStructuredText]: http://www.sphinx-doc.org/en/stable/rest.html
[sphinx-autobuild]: https://pypi.python.org/pypi/sphinx-autobuild
[recommonmark]: https://github.com/rtfd/recommonmark
[cadnano/docs/docs.md]: https://github.com/cadnano/cadnano2.5/blob/master/docs/docs.md
[cadnano/docs/scripting.md]: https://github.com/cadnano/cadnano2.5/blob/master/docs/scripting.md
[Makefile]: https://github.com/cadnano/cadnano2.5/blob/master/docs/Makefile
[conf.py]: https://github.com/cadnano/cadnano2.5/blob/master/docs/conf.py
