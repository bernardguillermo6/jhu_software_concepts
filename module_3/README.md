Bernard Guillermo (bguille3@jh.edu)


# Module 3: SQL Data Analysis - Due September 14, 2025

This assignment is practices querying relational databases and connecting them to a web application. We're using the data that we collected in module 2 and answering questions in a web application. We're then building out connection to scrape new data and integrate it into our analysis.

---

## Approach
The main approach to this module is to build on top of what we did with the last two modules. I locally installed Postgresql and loaded the cleaned jsonl file that we generated at the end of module 2. I then did some quick analysis on the data before starting to answer the questions. I then leveraged the templates that we used within module 1 to build the website for this module. 

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
To run the project, run:
```
python run.py
```
Then go to http://127.0.0.1:8080/


## Project Structure
```
module_2/
│── run.py             # Flask entry point
│── query_data.py      # Question and answers to the prompt
│── load_data.py       # Functions to load data from jsonl to psql 
│── db.py              # Functions to initialze db connections
│── module_2/          # Libraries (scrape, clean, and LLM) from module_2
│── static/            # CSS
│── templates/         # HTML templates
│── requirements.txt   # Python package dependencies
│── README.md          # Project documentation
```



