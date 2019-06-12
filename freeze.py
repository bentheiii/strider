import subprocess
import os.path as path

import strider

single_file = True
name_prefix = 'strider-'
icon_path = r'icon.ico'

prefix = ['python -O -m PyInstaller strider/__main__.py']

name = name_prefix + strider.__version__
prefix.append('-n "' + name + '"')

if single_file:
    prefix.append('-F')

if icon_path and path.exists(icon_path):
    prefix.append('-i "' + icon_path + '"')

command = ' '.join(prefix)
print(command)
subprocess.run(command)
