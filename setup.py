from setuptools import setup, find_packages

setup(
    name='hf_backup_tool',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'PyQt6',
        'qt_material',
        'huggingface_hub',
        'requests',  # Added requests
    ],
)