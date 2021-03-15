from distutils.core import setup, Extension
from Cython.Build import cythonize
import numpy as np
import os
import pathlib
currdir = pathlib.Path(__file__).parent
os.environ['CC'] = 'gcc'
os.environ['CXX'] = 'g++'
graph_software_dir = currdir.parent / 'include' 

extensions = [
    Extension(
        name='multicut',
        include_dirs=[np.get_include(), '{}/graph/include'.format(graph_software_dir)],
        sources=[currdir/'multicut.pyx', currdir/'cpp-multicut.cpp'],
        extra_compile_args=['-O4', '-std=c++11'],
        language='c++'
    ),
    Extension(
        name='lifted_multicut',
        include_dirs=[np.get_include(), '{}/graph/include'.format(graph_software_dir)],
        sources=[currdir/'lifted_multicut.pyx', currdir/'cpp-lifted-multicut.cpp'],
        extra_compile_args=['-O4', '-std=c++11'],
        language='c++'
    )
]

setup(
    name='algorithms',
    ext_modules = cythonize(extensions)
)
