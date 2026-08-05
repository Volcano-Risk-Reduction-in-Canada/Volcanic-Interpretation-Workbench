import json
import setuptools

with open("package.json") as f:
    package = json.load(f)

package_name = package["name"].replace(" ", "_").replace("-", "_")

setuptools.setup(
    name=package_name,
    version=package["version"],
    author=package.get("author"),
    description=package.get("description", package_name),
    packages=[package_name],
    include_package_data=True,
    license=package.get("license", "MIT"),
    install_requires=["dash>=2.0.0"],
)
