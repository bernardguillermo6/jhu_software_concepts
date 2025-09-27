Bernard Guillermo (bguille3@jh.edu)


# Module 5: Software Assurance, Static Code Analysis, and SQL Injections - Due September 28, 2025

In this assignment, we practiced carrying out software assurance practices
including input validation, static code analysis, dependency analysis, and virtual environment
configuration. This work helps secure queries to a database and defend the Grad Cafe application
from potential injection attacks.

---

## Approach
I approached this module by copying everything from module_4 into a module_5 folder. First, I installed black to help
with formatting and isort to take care of import order. Then, I installed pylint to lint all the files and correct any issues that were flagged. Because docs used Sphinx for the doc creation, I excluded it from the linting. I then went through and added SQL injection defenses. Afterwards, I created the Python dependency graph. Lastly, I installed and used Synk to check for malicious packages.


## Installation

Clone the repository:
```
git clone https://github.com/bernardguillermo6/jhu_software_concepts.git
cd module_4
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
To run pylint and confirm 10.0 score, go to the `module_5` folder and run
```
pylint .
```

To confirm tests still pass, go to the `module_5` folder and run
```
pytest -m "web or buttons or analysis or db or integration"
```
The application can be run using `python -m src.run`


## Project Structure
```
module_5/
│── docs/                      # Sphinx project
│── src/                       # Application code
│── tests/                     # Pytest testing suite
│── pytest.ini                 # Pytest config file
│── requirements.txt           # Python package dependencies
│── dependency.svg             # Python dependency graph
│── module_5-dependencies.pdf  # PDF explaining Python dependencies
│── pyproject.toml             # Python setup file
│── README.md                  # Project documentation
```



