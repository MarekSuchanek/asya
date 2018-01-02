from setuptools import setup, find_packages

with open('README.rst') as f:
    long_description = ''.join(f.readlines())

setup(
    name='asya',
    version='0.1',
    keywords='github issues social search asyncio comments issues',
    description='Asynchronously your acquaintances from GitHub issues',
    long_description=long_description,
    author='Marek Suchánek',
    author_email='suchama4@fit.cvut.cz',
    license='MIT',
    url='https://github.com/MarekSuchanek/asya',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'asya = asya:main',
        ]
    },
    install_requires=[
        'aiohttp',
        'requests',
        'click'
    ],
    python_requires='>=3.4',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications',
        'Topic :: Sociology',
    ],
)
