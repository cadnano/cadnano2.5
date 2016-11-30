# Deployment guide

## Build binaries

Install `cx_Freeze` :

```sh
pip install cx_Freeze
```

Note : if you want to freeze using Python 3.5 you should use the last `cx_Freeze` dev version : `pip install hg+https://bitbucket.org/anthony_tuininga/cx_freeze#egg=default`

Then you can build `cadnano` with :

```
python setup-freeze.py build
```

Note that the binaries generated are specific to the platform used to execute the build step and it's not possible to generate binaries for other platforms.

Then you can generate zip file containing all the required files and ready to be deployed.

```
python setup-freeze.py bdist --format=zip
```

The zip file is available in the `dist/` folder.


## Deploy binaries

Generated files for Windows, Mac OS X and Linux can be uploaded using the GitHub releasing system at https://github.com/cadnano/cadnano2.5/releases.
