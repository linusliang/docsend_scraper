from setuptools import setup

with open('requirements.txt', 'r') as f:
    install_requires = [req.strip() for req in f]
with open('dev-requirements.txt', 'r') as f:
    tests_require = [req.strip() for req in f]

config = {
    'name': 'api',
    'version': '0.0.1',
    'scripts': ['application.py'],
    'install_requires': install_requires,
    'tests_require': tests_require,
    'setup_requires': ['pytest-runner'],
    'author': "Michael Benoit",
    'description': 'docsend scraper'
}

setup(**config)