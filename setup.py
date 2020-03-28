# type: ignore
import setuptools

setuptools.setup(
    name="pyring",
    version="0.0.12",
    author="Jacob Richter",
    author_email="jaycorichter@gmail.com",
    description="A ring buffer (circular buffer, circular queue, cyclic buffer) implemented in pure python. Includes flexible locking, waiting, and Disruptor variants.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jaycosaur/pyring",
    packages=setuptools.find_packages(),
    package_data={"pyring": ["py.typed"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
