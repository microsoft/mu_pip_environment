# Publishing Project Mu Pip Environment

The MuEnvironment is published as a pypi (pip) module.  The pip module is named __mu_environment__.  Pypi allows for easy version management, dependency management, and sharing.

Publishing/releasing a new version is generally handled thru a server based build process but for completeness the process is documented here.

## Steps

!!! Info
    These directions assume you have already configured your workspace for developing.  If not please first do that.  Directions on the [developing](developing.md) page.

1. Install tools for publishing

``` cmd
pip install --upgrade -r requirements.publisher.txt
```

2. Build a wheel

``` cmd
python setup.py sdist bdist_wheel
```

3. Publish the wheel/distribution to pypi

``` cmd
twine upload dist/*
```

## Server Build

## Release Checklist


