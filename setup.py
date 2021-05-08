from os import path
from sys import version

from setuptools import setup

if version < '3':
    raise RuntimeError("Python 3 is, at least, needed")

this = path.abspath(path.dirname(__file__))
with open(path.join(this, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='pyCloudFlareUpdater',
    version='2.0.0',
    packages=['pyCloudFlareUpdater',
              'pyCloudFlareUpdater.values',
              'pyCloudFlareUpdater.network',
              'pyCloudFlareUpdater.preferences',
              'pyCloudFlareUpdater.logging_utils'],
    url='https://gitlab.javinator9889.com/ddns-clients/pyCloudFlareUpdater',
    license='GPLv3',
    author='Javinator9889',
    author_email='contact@javinator9889.com',
    description='DDNS service for dynamically update CloudFlare \'A\' Records',
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=False,
    zip_safe=True,
    download_url="https://github.com/ddns-clients/pyCloudFlareUpdater/archive/refs/heads/master.zip",
    entry_points={
        'console_scripts': [
            'cloudflare_ddns=pyCloudFlareUpdater.__main__:parser']
    },
    install_requires=['daemonize'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
