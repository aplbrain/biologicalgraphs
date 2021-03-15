from distutils.core import setup, Extension
from Cython.Build import cythonize
import numpy as np
import pathlib
currdir = pathlib.Path(__file__).parent

extensions = [
    Extension(
        name='generate_skeletons',
        include_dirs=[np.get_include()],
        sources=[str(currdir/'generate_skeletons.pyx'), str(currdir/'cpp-thinning.cpp'), str(currdir/'cpp-upsample.cpp')],
        extra_compile_args=['-O4', '-std=c++0x'],
        language='c++'
    )
]

setup(
    name='skeletonization',
    ext_modules=cythonize(extensions)
)
