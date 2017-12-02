import shutil
import os

sysroot = os.environ['SYSROOT']
INSTALL_DIR = 'C:\\Users\\Nick\\Documents\\GitHub\\cadnano2.5\\pyqtdeploy\\build\\release'


def scrapeExtensionFiles(sysroot, modules, ext, install_dir, version='3.5'):
    source_dir = os.path.join(sysroot, 'lib', 'python%s' % version, 'site-packages')
    copy_list = []
    for module_name in modules:
        mod_dir = os.path.join(source_dir, module_name)
        for root, dirs, files in os.walk(mod_dir):
            for fn in files:
                if os.path.splitext(fn)[1] == ext:
                    new_root = root
                    split_on_dot = fn.split('.')
                    out_fn = split_on_dot[0] + ext
                    append_str = os.path.basename(new_root)
                    while append_str != module_name:
                        out_fn = append_str + '.' + out_fn
                        new_root = os.path.dirname(new_root)
                        append_str = os.path.basename(new_root)
                    out_fn = append_str + '.' + out_fn
                    print(out_fn)
                    copy_list.append((os.path.join(root, fn), out_fn))

    for item in copy_list:
        src, dst_fn = item
        dst = os.path.join(install_dir, dst_fn)
        shutil.copyfile(src, dst)


if __name__ == '__main__':
    scrapeExtensionFiles(sysroot, ['numpy', 'pandas', 'numexpr', 'bottleneck'], '.pyd', INSTALL_DIR)
