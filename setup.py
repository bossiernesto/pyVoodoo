from setuptools import setup,find_packages
import os

PATH = os.path.dirname(os.path.abspath(__file__))
templates_dir= os.path.join(PATH, ".")
templates_files = [os.path.join(templates_dir, file) for file in os.listdir(templates_dir)]

setup(name='PyVoodoo',
    version='0.1',
    description='Small library to generate code and bytecode dynamically',
    author='Ernesto Bossi',
    author_email='bossi.ernestog@gmail.com',
    license='GPLv3',
    keywords='',
    packages=find_packages(exclude=["test"]),
    data_files=[
        (templates_dir, templates_files)
    ],
    install_requires=['pyMetaBuilder']
)
