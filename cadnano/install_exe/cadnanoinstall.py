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
        print("Copying from ... :", cadnano_binary_fps)
        print("... to:", new_cadnano_binary_fps)
        [shutil.copy2(o, d) for o, d in zip(cadnano_binary_fps,
                                               new_cadnano_binary_fps)]
        list(map(makeExecutable, new_cadnano_binary_fps))
# end def

if __name__ == '__main__':
    print("running setup of environment")
    post_install()