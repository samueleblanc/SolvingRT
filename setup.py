"""
MIT License

Copyright (c) [2022] [Samuel Leblanc]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

#!/usr/bin/env

import os
from setuptools import setup


def readme(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()


setup(name="SolvingRT",
      version="0.1.0",
      description="Measure certain aspect of exercise mechanics in a non-intrusive way",
      long_description=readme("README.md"),
      author="Samuel Leblanc",
      author_email="samuel.solving.rt@gmail.com",
      url="https://github.com/samueleblanc/SolvingRT",
      license="MIT",
      keywords=["resistance", "training", "video", "exercise"],
      packages=["solvingrt"],
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License"
      ],
      install_requires=["numpy", "opencv-python", "mediapipe", "matplotlib"],
      python_requires=">=3.8"
      )
