Bernard Guillermo (bguille3@jh.edu)


# Module 4: SQL Data Analysis - Due September 22, 2025

In this assignment, we're building an automated test suite to cover the application we built in module 3. It covers everything from the Flask page, interactive buttons, analysis outputs/formatting, and database writes. We also are publishing CI/CD tests to the Github repository and publishing documentation on Read the Docs using Sphinx.

---

## Approach
I approached this module by copying everything from module 3 into a module_4 folder. Then, I moved all the files into a src directory and created pytests in a test directory. After the tests were done, I also added a Github action so we have CI/CD tests. Lastly, I used Sphinx to create the documentation and publish to Read the Docs.


## Installation

Clone the repository:
```
git clone https://github.com/bernardguillermo6/jhu_software_concepts.git
cd module_3
```

Create a virtual environment:
```
python -m venv venv
source venv/bin/activate
```

Install dependencies:
```
pip install -r requirements.txt
```
This application was built using Python 3.12.5

## Usage
To run the tests, go to the `module_4` folder and run
```
pytest -m "web or buttons or analysis or db or integration"
```
The application itself can be run using `python -m src.run`

Documentation is published to Read the Documents [here] (https://jhu-software-concepts-bguillermo.readthedocs.io/en/latest/).

## Project Structure
```
module_4/
│── docs/                # Sphinx project
│── src/                 # Application code
│── tests/               # Pytest testing suite
│── pytest.ini           # Pytest config file
│── requirements.txt     # Python package dependencies
│── coverage_summary.txt # Documentation confirming 100% test coverage
│── actions_success.png  # Screenshot confirm Github actions successful run
│── README.md            # Project documentation
```



