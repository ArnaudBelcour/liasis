import os

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst'), encoding='utf-8') as readme_file:
      readme = readme_file.read()

with open(os.path.join(os.path.dirname(__file__), 'requirements.txt'), encoding='utf-8') as requirement_file:
      requirements = requirement_file.read().splitlines()

setup(name='liasis',
      description='Singular Enrichment Analysis',
      long_description=readme,
      version='0.2.6.1',
      url='https://github.com/ArnaudBelcour/liasis',
      author='A. Belcour',
      author_email='arnbpro@gmail.com',
      license='GNU Affero General Public License v3.0',
      classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Audience
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',

        # License
        'License :: OSI Approved :: GNU Affero General Public License v3',

        # Environnement, OS, languages
        'Programming Language :: Python :: 3'
      ],
      packages=['liasis'],
      install_requires=requirements,
)
