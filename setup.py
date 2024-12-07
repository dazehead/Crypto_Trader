from setuptools import setup, find_packages

setup(
    name="coinbase_trader",            # Name of your project
    version="1.0.0",                   # Version of your project
    packages=find_packages(),          # Automatically find and include all packages
    install_requires=[                 # List dependencies if any
        # Add dependencies here, e.g.:
        # "numpy>=1.21.0",
        # "pandas>=1.3.0",
    ],
    include_package_data=True,         # Include files like `__init__.py` in your packages
)