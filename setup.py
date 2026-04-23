from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="parasramka_erpnext",
    version="0.0.1",
    description="Custom ERPNext app for Parasramka Engineering",
    author="Parasramka Engineering Pvt. Ltd.",
    author_email="aviral.parasramka@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)