import os
import setuptools

SETUPDIR = os.path.dirname(__file__)

with open(os.path.join(SETUPDIR, 'README.md'), 'r') as f:
    long_description = f.read()

PKGNAME = "teap"
packages = [f"{PKGNAME}"]

for p in setuptools.find_packages(where="src/web/backend", exclude=["tests"]):
    packages.append(f"{PKGNAME}.{p}")

setuptools.setup(
    name='teap',
    version='0.0.1',
    author='EnterpriseyIntranet',
    description="Integration of LDAP and Nextcloud, Rocketchat",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/EnterpriseyIntranet/teap",
    packages=packages,
    package_dir={"teap": "src/web/backend"},
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        "Operating System :: OS Independent",
    ],
)
