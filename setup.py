"""Open Peer Power Supervisor setup."""
from setuptools import setup

from supervisor.const import SUPERVISOR_VERSION

setup(
    name="Supervisor",
    version=SUPERVISOR_VERSION,
    license="BSD License",
    author="The Open Peer Power Authors",
    author_email="hello@open-peer-power.io",
    url="https://open-peer-power.io/",
    description=("Open-source private cloud os for Open-Peer-Power" " based on OppOS"),
    long_description=(
        "A maintainless private cloud operator system that"
        "setup a Open-Peer-Power instance. Based on OppOS"
    ),
    classifiers=[
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.8",
    ],
    keywords=["docker", "open-peer-power", "api"],
    zip_safe=False,
    platforms="any",
    packages=[
        "supervisor",
        "supervisor.docker",
        "supervisor.addons",
        "supervisor.api",
        "supervisor.dbus",
        "supervisor.dbus.payloads",
        "supervisor.dbus.network",
        "supervisor.discovery",
        "supervisor.discovery.services",
        "supervisor.services",
        "supervisor.services.modules",
        "supervisor.openpeerpower",
        "supervisor.host",
        "supervisor.misc",
        "supervisor.utils",
        "supervisor.plugins",
        "supervisor.snapshots",
        "supervisor.store",
    ],
    include_package_data=True,
)
