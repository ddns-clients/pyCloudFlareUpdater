from os import path
from sys import version

from setuptools import setup

if version < '3':
    raise RuntimeError("Python 3 is, at least, needed")

this = path.abspath(path.dirname(__file__))
with open(path.join(this, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='pyCloudflareUpdater',
    version='2.0.0',
    packages=['pyCloudflareUpdater',
              'pyCloudflareUpdater.values',
              'pyCloudflareUpdater.network',
              'pyCloudflareUpdater.preferences',
              'pyCloudflareUpdater.logging_utils'],
    url='https://github.com/ddns-clients/pyCloudFlareUpdater',
    license='GPLv3',
    author='Javinator9889',
    author_email='contact@javinator9889.com',
    description='DDNS service for dynamically update Cloudflare \'A\' Records',
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=False,
    zip_safe=True,
    download_url="https://github.com/ddns-clients/pyCloudFlareUpdater/archive/refs/heads/master.zip",
    entry_points={
        'console_scripts': [
            'cloudflare-ddns=pyCloudflareUpdater.main:parser']
    },
    install_requires=['python-daemon>=2,<3',
                      'requests>=2,<3',
                      'CacheControl>=0.12',
                      'keyring>=23',
                      'keyrings.cryptfile>=1,<2',
                      'cryptography>=3'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)
