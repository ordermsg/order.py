from distutils.core import setup
import setuptools

with open('README.md', 'r') as d:
    detail = d.read()

setup(
    name = 'order.py',
    packages = ['order'],
    version = '0.0.3',
    license='MIT',
    description = 'Official Order Python API wrapper',
    author = 'portasynthinca3',
    author_email = 'portasynthinca3@gmail.com',
    url = 'https://github.com/ordermsg/order.py',
    download_url = 'https://github.com/ordermsg/order.py/archive/0.0.1.tar.gz',
    keywords = ['api', 'api-client'],
    long_description=detail,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)