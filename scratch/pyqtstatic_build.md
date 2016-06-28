# `pyqtdeploy` instructions as of Qt 5.6.1

## Setup on Windows (could put qmake on the PATH)

In powershell:

	Set-Item Env:SYSROOT "C:\Users\Nick\Documents\GitHub\cadnano2.5\pyqtdeploy\winsysroot"

In `cmd.exe`:
	set SYSROOT="C:\Users\Nick\Documents\GitHub\cadnano2.5\pyqtdeploy\winsysroot"


Install System Python to `SYSROOT`:

	pyqtdeploycli  --sysroot $Env:SYSROOT --package python --target win-64 --system-python 3.5 install
	pyqtdeploycli --enable-dynamic-loading --sysroot $Env:SYSROOT --package python --target win-64 --system-python 3.5 install

Install Static qt 5

C:/qt-everywhere-opensource-src-5.6.1/qt5.6.1src/configure.bat -platform win32-msvc2015 -prefix %SYSROOT%/qt5.6 -static -release -nomake examples -skip qtactiveqt -skip qtandroidextras -skip qtconnectivity -skip qtdeclarative -skip qtdoc -skip qtenginio -skip qtgraphicaleffects -skip qtlocation -skip qtquickcontrols -skip qtquickcontrols2 -skip qtscript -skip qtsensors -skip qtserialport -skip qttools -skip qttranslations -skip qtwayland -skip qtx11extras -skip qtandroidextras -skip qtxmlpatterns -skip qtwebchannel -opengl desktop


~/Downloads/qt5.6.1src/qt-src-5.6.1/configure -prefix ~/qt5.6.1 -release -nomake examples -skip qtactiveqt -skip qtandroidextras -skip qtconnectivity -skip qtdeclarative -skip qtdoc -skip qtenginio -skip qtgraphicaleffects -skip qtlocation -skip qtquickcontrols -skip qtquickcontrols2 -skip qtscript -skip qtsensors -skip qtserialport -skip qttools -skip qttranslations -skip qtwayland -skip qtx11extras -skip qtandroidextras -skip qtxmlpatterns -skip qtwebchannel -opengl desktop

nmake
nmake install


C:\Users\Nick\Downloads\qt-src-5.5.1\qt-src-5.5.1\configure.bat -platform win32-msvc2015 -prefix %QT551% -release -nomake examples -skip qtactiveqt -skip qtandroidextras -skip qtconnectivity -skip qtdeclarative -skip qtdoc -skip qtenginio -skip qtgraphicaleffects -skip qtlocation -skip qtquickcontrols -skip qtscript -skip qtsensors -skip qtserialport -skip qttools -skip qttranslations -skip qtwayland -skip qtx11extras -skip qtmacextras -skip qtxmlpatterns -skip qtwebchannel -opengl desktop


In SIP source directory

	pyqtdeploycli --package sip --target win-64 configure
	python configure.py --static --sysroot=$Env:SYSROOT --no-tools --use-qmake --configuration=sip-TARGET.cfg
	python C:\Users\Nick\Downloads\sip-4.18\sip4.18\configure.py --static --sysroot=%SYSROOT% --no-tools --use-qmake --configuration=sip-win.cfg
	qmake
	nmake
	nmake install

In PyQt5 source directory

	pyqtdeploycli --package pyqt5 --target win-64 configure

	python C:\Users\Nick\Downloads\PyQt5_gpl-5.6\PyQt5_gpl-5.6\configure.py --static --sysroot=%SYSROOT% --no-tools --no-qsci-api --no-designer-plugin --no-qml-plugin --qmake=%SYSROOT%/qt5.6/bin/qmake.exe --sip="C:\Anaconda3\sip.exe" --configuration=pyqt5-win.cfg --enable=QtCore --enable=QtGui --enable=QtSvg --enable=QtOpenGL --enable=QtWidgets --enable=QtPrintSupport --enable=QtTest --enable=QtWinExtras --bindir=$Env:SYSROOT --destdir=%SYSROOT%\lib\python3.5\site-packages
	nmake
	nmake install


	# window need to rename qmake in Anaconda\Library\bin since Anaconda adds it to the top of the PATH at runtime
	# so configure.py works since PyQt5 on windows makes sure you have only one qmake.exe on the PATH
	python C:\Users\Nick\Downloads\PyQt-gpl-5.5.1\PyQt-gpl-5.5.1\configure.py --no-qsci-api --no-designer-plugin --no-qml-plugin --sip="C:\Anaconda3\sip.exe" --enable=QtCore --enable=QtGui --enable=QtSvg --enable=QtOpenGL --enable=QtWidgets --enable=QtPrintSupport --enable=QtTest --enable=QtWinExtras

		python configure.py --no-qsci-api --no-designer-plugin --no-qml-plugin --sip="C:\Anaconda3\sip.exe" --enable=QtCore --enable=QtGui --enable=QtSvg --enable=QtOpenGL --enable=QtWidgets --enable=QtPrintSupport --enable=QtTest --enable=QtWinExtras

	--disable=QAxContainer
	--disable=QtDesigner
	--disable=QtLocation
	--disable=QtPositioning
	--disable=QtQml
	--disable=QtQuick
	--disable=QtQuickWidgets
	--disable=QtWebChannel
	--disable=QtWebSockets
	--disable=QtXml
	--disable=QtXmlPatterns
	--disable=_QOpenGLFunctions_ES2

	python configure.py --static --no-tools --no-qsci-api --no-designer-plugin --no-qml-plugin --qmake=/Users/nick/qt5.6.1/bin/qmake --sip=/Users/nick/virtualenvs/radnano35/bin/sip --enable=QtCore --enable=QtGui --enable=QtSvg --enable=QtOpenGL --enable=QtWidgets --enable=QtPrintSupport --enable=QtTest --enable=QtMacExtras

## OS X modification to shared libraries
Copy qt dynamic build library to python root, i.e. root of virtualenv, etc
basically `sys.base_prefix` and then for each *.so library call `install_name_tool`
as follows (example QtWidgets):

	install_name_tool -add_rpath @executable_path/../Qt5.5/lib ~/virtualenvs/testqtpy/lib/python3.5/site-packages/PyQt5/QtWidgets.so

and we could even remove the original rpath.

## Windows modifications to support shared libraries

	Just put dlls in same directory as python libs.


# Modifications to Numpy and Pandas

	In the SYSROOT copies of these files comment out

	pandas/__init__.py

			# from pandas.io.api import *

		and

			# define the testing framework
			# import pandas.util.testing
			# from pandas.util.nosetester import NoseTester
			# test = NoseTester().test
			# del NoseTester

	for pandas make sure not to copy pyd or so files bootstrap files like
	hashtable.py and algos.py since they get in the way

	numpy\testing\__init__.py

		# from .nosetester import run_module_suite, NoseTester as Tester
		class Tester():
			bench = None
			test = None


C:\Users\Nick\Documents\GitHub\rcedit\Default>rcedit.exe C:\Users\Nick\Documents\GitHub\cadnano2.5\cadnano\install_exe\cadnano.exe --set-icon C:\Users\Nick\Downloads\radnano-app-icon.ico