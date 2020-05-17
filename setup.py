import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="runremotely",
    version="0.1.1",
    author="Odyssée",
    author_email="otremoulis@gmail.com",
    description="Automatically launch AWS ec2 instance to fit your ML model.",
    long_description_content_type="text/markdown",
    url="https://github.com/OdysseeT/runremotely.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
