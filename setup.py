
import setuptools

with open('./README.md') as rfile:
    long_desc = rfile.read()

setuptools.setup(
    name='jcfg',
    version='0.7.0',
    description='A json-based configuration helper lib for python',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    author='chkap',
    author_email='d47bc0@gmail.com',
    url='https://github.com/chkap/jcfg',
    packages=['jcfg'],
    install_requires=[
        "jstyleson"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license='MIT license'
    )

