# Python Unit tests :pencil2:

This directory contains all the Python unit tests we built to ensure quality and robustness of our algorithm. We build the tests using the Python libraries called `unittest` and `pytest`, feeding it with dummy data. To execute them run the following commands from the root folder of this Git repo:

```
pytest                                          # for Plaid
python -m unittest -v unit_tests                # for both Coinbase & Covalent
```

> :warning: `unittest` relies on imported test data (_json_ files). We crafted some fake and anonimized test data-sets with the explicit goal of executing unit tests. Find these data sets in the `tests` directory.



