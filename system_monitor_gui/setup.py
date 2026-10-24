from glob import glob
import os

from setuptools import setup

package_name = "system_monitor_gui"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="lotus1282",
    maintainer_email="lotus1282@users.noreply.github.com",
    description="Qt dashboard and psutil publisher for live ROS 2 system metrics.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "system_status_publisher = system_monitor_gui.publisher_node:main",
            "system_status_gui = system_monitor_gui.gui_node:main",
        ],
    },
)
