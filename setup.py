import setuptools
import strider

setuptools.setup(
    name='strider',
    version=strider.__version__,
    author=strider.__author__,
    packages=['strider'],  # be sure to exclude strider.__dev__
    install_requires=['opencv-python>=3', 'sortedcontainers>=2'],
    python_requires='>=3.6.0'
)
