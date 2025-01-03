from setuptools import setup, Extension
import numpy
import datetime
import pathlib
from Cython.Build import cythonize

# python setup.py build_ext --inplace

def lib_file_list(dir_list):
    lib_file_list = []
    for dir in dir_list:
        dir_path = pathlib.Path(dir)
        if dir_path.exists():
            lib_files = list(dir_path.glob("**/*.lib"))
            for lib_file in lib_files:
                lib_file_list.append(lib_file.name.split('.')[0])
    
    return lib_file_list
            
lib_list = [
    "c10",
    "c10_cuda",
    "torch",
    "torch_cpu",
    "torch_cuda",
    "caffe2_nvrtc"
]
lib_list.extend(lib_file_list([
]))

wrapper_ext = [
    Extension("train_wrapper", ["train_wrapper.pyx"],
    include_dirs=[
        numpy.get_include(),
        "D:/Libraries/boost_1_81_0/",
        "D:/Libraries/libtorch/include",
        "D:/Libraries/libtorch/include/torch/csrc/api/include",
        "D:/Libraries/tqdm.cpp-master/include",
        "D:/Libraries/libnpy-master/include",
    ],
    libraries=lib_list,
    library_dirs=[
        "D:/Libraries/libtorch/lib",
        "D:/Libraries/boost_1_81_0/stage/lib"
    ]),
    Extension("inference_wrapper", ["inference_wrapper.pyx"],
    include_dirs=[
        numpy.get_include(),
        "D:/Libraries/boost_1_81_0/",
        "D:/Libraries/libtorch/include",
        "D:/Libraries/libtorch/include/torch/csrc/api/include",
        "D:/Libraries/tqdm.cpp-master/include",
        "D:/Libraries/libnpy-master/include",
    ],
    libraries=lib_list,
    library_dirs=[
        "D:/Libraries/libtorch/lib",
        "D:/Libraries/boost_1_81_0/stage/lib"
    ])
]

extensions = [
    Extension("sentence", ["sentence.pyx"],
              include_dirs=[numpy.get_include()]),
    Extension("cjamo", ["cjamo.pyx"]),
    Extension("cvocabulary", ["cvocabulary.py"]),
    Extension("cmetric", ["cmetric.pyx"],
              include_dirs=[numpy.get_include()])
]
# jamo extra_compile_args=["/utf-8"]
extensions.extend(wrapper_ext)

setup(
    name="cython_module",
    ext_modules=cythonize(extensions, gdb_debug=True),
    zip_safe=False,
)

now = datetime.datetime.now()
print(now)