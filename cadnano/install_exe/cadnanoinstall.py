import sys
import os.path
import shutil
import os

pjoin = os.path.join

INSTALL_EXE_PATH =          os.path.abspath(os.path.dirname(__file__))

if sys.platform == 'win32':
    path_scheme = {
        'scripts': 'Scripts',
    }
    cadnano_binaries = ['cadnano.exe', 'cadnano-script.py']
    cadnano_binary_fps = [pjoin(INSTALL_EXE_PATH, fn) for fn in cadnano_binaries]
else:
    path_scheme = {
    'scripts': 'bin',
    }
script_path = pjoin(sys.exec_prefix, path_scheme['scripts'])

# Insure that the copied binaries are executable
def makeExecutable(fp):
    ''' Adds the executable bit to the file at filepath `fp`
    '''
    mode = ((os.stat(fp).st_mode) | 0o555) & 0o7777
    print("Adding executable bit to %s (mode is now %o)" % (fp, mode))
    os.chmod(fp, mode)
# en def

def post_install():
    if sys.platform == 'win32':
        new_cadnano_binary_fps = [pjoin( script_path, fn)
                                         for fn in cadnano_binaries]
        # print("Copying from ... :", cadnano_binary_fps)
        # print("... to:", new_cadnano_binary_fps)
        # [shutil.copy2(o, d) for o, d in zip(cadnano_binary_fps,
        #                                        new_cadnano_binary_fps)]
        # list(map(makeExecutable, new_cadnano_binary_fps))
        print("Installing Start menu shortcut...")
        import winshell
        link_filepath = os.path.join(winshell.programs(), "cadnano.lnk")
        import cadnano
        CN_PATH = os.path.dirname(os.path.abspath(cadnano.__file__))
        ICON_PATH = pjoin(CN_PATH, 'gui', 'ui',
                    'mainwindow', 'images', 'radnano-app-icon.ico')
        with winshell.shortcut(link_filepath) as link:
          link.path = new_cadnano_binary_fps[0]
          link.description = "Shortcut to cadnano"
          link.icon_location = (ICON_PATH, 0)
          # link.arguments = ""
        print("...Installation Complete")
    elif sys.platform == 'darwin':
        import cadnano.bin.appify as appify
        CN_BIN_PATH = os.path.dirname(os.path.abspath(appify.__file__))
        CN_PATH = os.path.dirname(CN_BIN_PATH)
        # rename script to fix Mac About menu text
        entry_path = pjoin(CN_BIN_PATH, 'radnano')
        shutil.copy2(pjoin(CN_BIN_PATH, 'main.py'), entry_path)
        ICON_PATH = pjoin(CN_PATH, 'gui', 'ui',
                            'mainwindow', 'images', 'radnano-app-icon.icns')
        appify.doAppify(entry_path, 'cadnano',
                            app_icon_path=ICON_PATH)
        print("...Installation Complete")
# end def

if __name__ == '__main__':
    print("running setup of environment")
    post_install()