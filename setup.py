from setuptools import setup

setup(
    name='pantra',
    version='1.0',
    packages=['pantra', 'pantra.components', 'pantra.components.grammar', 'pantra.contrib', 'pantra.jsmap',
              'pantra.models', 'pantra.trans'],
    #packages=find_packages('pantra'),
    url='https://github.com/zergos/pantra',
    license='Apache 2.0',
    author='Andrey Aseev',
    author_email='invent@zergos.ru',
    description='Python Full-stack Framework',
    install_requires=[
        'aiohttp==3.7.4.post0',
        'antlr4-python3-runtime==4.10',
        'cssutils==2.3.0',
        'requests==2.31.0',
        'libsass==0.22.0',
        'Babel>=2.9.1',
        'watchdog>=2.1.6',
        'quazydb @ git+https://github.com/zergos/quazydb',
    ],
    python_requires=">=3.10",
    entry_points={
        'console_scripts': [
            'pantra=pantra.management:execute_from_command_line',
        ],
    },
)
