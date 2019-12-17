# Contributing

To get setup in the environment and run the tests, take the following steps:

```bash
python3 -m venv env
source env/bin/activate
pip install -e '.[test]'

nosetests
flake8
```

Please format your code contributions with the ``yapf`` formatter:

```bash
yapf -i --style=pep8 pamqp
```

## Test Coverage

Pull requests that make changes or additions that are not covered by tests
will likely be closed without review.
