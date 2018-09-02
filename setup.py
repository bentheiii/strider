from pathlib import Path
import setuptools

import strider

setuptools.setup(
    name='strider',
    version=strider.__version__,
    author=strider.__author__,
    packages=['strider'],  # be sure to exclude strider.__dev__
    install_requires=['opencv-python>=3', 'sortedcontainers>=2'],
    python_requires='>=3.6.0',
    url='https://github.com/bentheiii/strider',
    license=Path('COPYRIGHT').read_text(),
    include_package_data=True,
    data_files=[
        ('', ['README.md', 'CHANGELOG.md', 'COPYRIGHT'])
    ]
)
