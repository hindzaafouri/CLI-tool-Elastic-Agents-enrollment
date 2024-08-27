from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read()

setup(
    name="enroll_agents_elk_tool",
    version="1.5.0",
    author="Hind Zaafouri",
    author_email="hindzaafouri19@gmail.com",
    license="Apache License 2.0",
    description="A versatile CLI tool designed to streamline the installation of Elastic Agents on selected Azure Virtual Machines within a specified subscription. This tool facilitates seamless integration of Azure VMs into an ELK stack, enabling comprehensive monitoring and log analysis across your cloud infrastructure.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hindzaafouri/Enroll-elastic-agents-CLI-tool.git",  # Replace with your repository URL
    packages=find_packages(include=["app", "app.*"]),
    # py_modules=['app'],
    install_requires=[requirements],
    python_requires=">=3.8.10",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    entry_points={"console_scripts": ["enroll_agents_elk=app.cli:main"]},
)
