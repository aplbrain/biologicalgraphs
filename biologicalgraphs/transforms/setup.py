from distutils.core import setup, Extension
from Cython.Build import cythonize
import numpy as np
import pathlib
currdir = pathlib.Path(__file__).parent

extensions = [
    Extension(
        name='distance',
        include_dirs=[np.get_include()],
        sources=[str(currdir/'distance.pyx'), str(currdir/'cpp-distance.cpp')],
        extra_compile_args=['-O4', '-std=c++0x'],
        language='c++'
    ),
    Extension(
        name='seg2gold',
        include_dirs=[np.get_include()],
        sources=[str(currdir/'seg2gold.pyx'), str(currdir/'cpp-seg2gold.cpp')],
        extra_compile_args=['-O4', '-std=c++0x'],
        language='c++'
    ),
    Extension(
        name='seg2seg',
        include_dirs=[np.get_include()],
        sources=[str(currdir/'seg2seg.pyx'), str(currdir/'cpp-seg2seg.cpp')],
        extra_compile_args=['-O4', '-std=c++0x'],
        language='c++'
    )
]

setup(
    name='transforms',
    ext_modules = cythonize(extensions)
)