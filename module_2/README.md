Bernard Guillermo (bguille3@jh.edu)


# Module 2: Web Scraping - Due September 7, 2025

This assignment is practices scraping data from websites. We're building a basic webscraper to grab admissions information from https://www.thegradcafe.com. Then, we have to clean and output a json file that stores all the student data. We then apply LLM model to normalize the degree and university data.

---

## Approach
The main approach to this module was to familiarize myself with thegradcafe.com. Looking at the survey page, you can see a lot of the data was unstructured, but you get multiple records per page. However, when I go to the detailed results page, the data is more structure, but it does not have all the data from the survey page. The challenge here is that you would need to scrape each results page individually. I ended up taking a dual approach and scraping what I needed to scrape from the survey page and then got the remaining data from the results page. I also ended up using threading so I could scrape individual results pages in a reasonable amount of time.

## Robots.txt
I've included a screenshot of the robots.txt file for thegradcafe.com. We can see that general agents are just not allowed on the /cgi-bin/ and /index-ad-test.php sites. Since we are not scraping those pages, we are fine to scape the pages we needed.

## Installation

Clone the repository:
```
git clone https://github.com/bernardguillermo6/jhu_software_concepts.git
cd module_2
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
python app.py
```

## Known Bugs
One thing to note is that the raw `applicant_data.json` file has 50k records but `llm_extend_applicant_data.jsonl` only has 40k records. I didn't have enough time to process the remaining 10k records.

## Project Structure
```
module_2/
│── app.py                          # the main file 
│── clean.py                        # file that houses functions to clean the data
│── scrape.py                       # file that houses functions to scrape the data
│── requirements.txt                # Python package dependencies
│── README.md                       # Project documentation
|── robots_txt_screenshot.png       # Screenshot to confirm robots.txt file
|── applicant_data.json             # Output of app.py
|── llm_extend_applicant_data.jsonl # Cleaned version of output of app.py
```



