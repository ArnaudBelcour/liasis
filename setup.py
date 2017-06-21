from setuptools import setup, Extension, Distribution

setup(name='liasis',
      description='Pandas-Based Single Enrichment Analysis',
      version='0.1.2',
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
      install_requires=[
            'numpy',
            'pandas>=0.19.2',
            'scipy',
            'statsmodels',
      ],
)
