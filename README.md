
# Jupman

A template manager for websites generated from Jupyter notebooks.

Jupman uses [NbSphinx](http://nbsphinx.readthedocs.io/) and builds with [ReadTheDocs](https://readthedocs.org), local sphinx, local Docker or Github Actions using [ReadTheDocs to Actions](https://github.com/DavidLeoni/readthedocs-to-actions)

## Official user manual: [jupman.softpython.org](https://jupman.softpython.org)

Replica for testing ReadTheDocs:

* https://jupman.readthedocs.io

Replicas for testing Github Action build, hosted on Github Pages:

* https://DavidLeoni.github.io/jupman/en/latest
* https://DavidLeoni.github.io/jupman/themed


## Developing


### Logging


You should use the logger defined in [jupman_tools](jupman_tools.py) module

To set the level and actually see some output, set `JUPMAN_LOG_LEVEL` environment variable

(not so clean but I spent way too much time fighting against the logging system)

### Testing

Run 

```bash
./test.sh
```

Running a sigle test with debugging logger:

```bash
JUPMAN_LOG_LEVEL=DEBUG python3 -m pytest _test/chapter_test.py::test_chapter_solution_web
```

