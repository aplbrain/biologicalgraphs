import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="biologicalgraphs", # Replace with your own username
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)