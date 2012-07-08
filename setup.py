"""
knyfe knyfe is a python utility for rapid exploration and preprocessing of datasets. Use it when you have some kind of dataset and you want to get a feel for how it is composed, run some simple tests on it, or prepare it for further processing. The great thing about knyfe is that you don't have to know much about how your dataset is designed. You shouldn't have to remember in which variable resides in which column of your data matrix or how your `structs` are nested. Just get shit done.

Links
`````

* `website & documentation <http://maebert.github.com/knyfe>`_
* `GitHub Repo <https://github.com/maebert/knyfe>`_

"""


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os
import sys

if sys.argv[-1] == 'publish':
    os.system("python setup.py bdist-egg upload")
    os.system("python setup.py sdist upload")
    sys.exit()

base_dir = os.path.dirname(os.path.abspath(__file__))

setup(
    name = "knyfe",
    version = "0.4.2",
    description = "A utility for rapid exploration and preprocessing of datasets.",
    packages = ['knyfe'],
    install_requires = ["numpy", "tablib", "simplejson"],
    package_data={'': ['*.md']},
    long_description=__doc__,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    ],
    # metadata for upload to PyPI
    author = "Manuel Ebert",
    author_email = "maebert@uos.de",
    license = "MIT License",
    keywords = "science data preprocessing".split(),
    url = "http://maebert.github.com/knyfe", 
)
