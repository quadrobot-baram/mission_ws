from setuptools import setup
from glob import glob
import os

package_name = 'img_capture'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='baram',
    maintainer_email='khg950520@gmail.com',
    description='Go2 image capture service using separated Unitree Python SDK process',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'img_capture_service = img_capture.img_capture_service:main',
            'go2_capture_once = img_capture.go2_capture_once:main',
        ],
    },
)
