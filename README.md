Attainia Django Extensions
======================================================================================================================

Attainia Django Extensions is a collection of helpful utilities to be used in Attainia Django/Rest Framework projects

What's included?

* Abstractions for Nameko RPC and Event subscription/dispatch
* Include Correlation ID on Nameko RPC and events
* Django REST Framework JWT authentication and permissions
* Utils for reading environment variables as dictionaries and lists
* Audit trail base model

Libraries used:

[Django REST Framework](https://github.com/encode/django-rest-framework)

[Django CID](https://github.com/snowball-one/cid)

[Nameko](https://github.com/nameko/nameko)

[Django Nameko](https://github.com/Attainia/django-nameko)

## Updating PyPI for a New Release of this Library


You will need to install Twine to update libraries in PyPI.  Twine is a utility for interacting with PyPI.  It's OK to install this globally on your machine.

```
pip3 install twine
```

Create a .pypirc configuration file in your

```
vi ~/.pypirc
```

The contents of this file should be as follows.

```
[pypi]
username = attainia
password = <password found in lastpass>
```

Set the permissions on the .pypirc file.

```
chmod 600 ~/.pypirc
```

From the library's project root directory upload the newest version of the library to PyPI.  Be sure the `attainia_django_extensions/__version__.py` reflects the correct version to be uploaded.

```
python3 setup.py upload
```
