from setuptools import setup

setup(
    name="cqcdata",
    version='0.0.1',
    packages=['cqcdata'],
    install_requires=[
        'Click',
        'requests',
        'xlrd',
        'pandas',
        'beautifulsoup4',
        'html5lib'
    ],
    entry_points='''
        [console_scripts]
        cqc_data=cqcdata.cli:cli
    ''',
)