# HPI Module explorer
## Purpose
This application is intended to make choosing modules for students at Hasso-Plattner-Institute easier. Currently, information on modules is scattered across a range of resources.

## Information retrieval
The scraping pipeline included in this project is able to parse the currently used resources, predominantly the HPI webpage. The information is then stored in a simple SQLite database.

## Usage
Users can search for courses using relevant filtering criteria like evaluation results, number of ECTS or module groups. They can then select modules they are interested in and add them to their list. On the "My modules" page, they can see an overview of all selected modules and how much ECTS the given modules gives for which kind of module group. This is relevant for deciding which modules to take in the future in order to fulfill course requirements.

## Installation
1. Clone this repo
2. Run `pipenv install` to install the dependencies
3. Running `pipenv run flask run` will start the local Flask server
4. Flask will display the IP, usually something like
    > Running on http://127.0.0.1:5000