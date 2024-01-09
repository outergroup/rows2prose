from setuptools import find_packages, setup

setup(name="rows2prose",
      version="0.1.0",
      description="Build text-centric visualizations with inline data",
      author="Marcus Lewis",
      url="https://rows2prose.org/",
      packages=find_packages(),
      package_data={'rows2prose': ['rows2prose/package_data/*',]},
      include_package_data=True,
      zip_safe=False,
)
