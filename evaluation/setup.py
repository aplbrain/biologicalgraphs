from distutils.core import setup, Extension
from Cython.Build import cythonize
import numpy as np
import pathlib
currdir = pathlib.Path(__file__).parent

extensions = [
    Extension(
        name='comparestacks',
        include_dirs=[np.get_include()],
        sources=[str(currdir/'comparestacks.pyx'), str(currdir/'cpp-comparestacks.cpp')],
        extra_compile_args=['-O4', '-std=c++0x'],
        language='c++'
    ),
]

setup(
    name='comparestacks',
    ext_modules = cythonize(extensions)
)
