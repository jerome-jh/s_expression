import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "s_expression",
    version = "0.0.1",
    author = "jerome-jh",
    author_email = "github",
    description = ("S-expressions for data serialization."),
    license = "GPLv3",
    keywords = "S-expression serialization parser",
    url = "https://github.com/jerome-jh/s_expression",
    packages=['test'],
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPLv3 License",
    ],
    ## Not sure it is required: never tested on Python2
    python_requires='>=3',
    test_suite="test.test"
)
