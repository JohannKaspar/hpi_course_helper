import requests
from bs4 import BeautifulSoup
import re

def get_module_links(url, host="https://hpi.de"):
    """
    Retrieves all module links from the given url.
    """
    
    # Send a GET request to the given url
    response = requests.get(url)

    # list of courses
    modules = []

    # Check if the response status code is 200 (OK)
    if response.status_code == 200:
        # Parse the HTML content of the response using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the div with class "tx-ciuniversity"
        university_div = soup.find('div', class_='tx-ciuniversity')
        
        if university_div:
            # Find the table with class "contenttable contenttable-0 table"
            table = university_div.find('table', class_='contenttable contenttable-0 table')
            
            if table:
                # Find all links in the left column of the table
                links = table.select('td:nth-child(1) a')
                
                for link in links:
                    href = link.get('href')
                    
                    # Add the link to the list of courses
                    modules.append(host + href)
            else:
                print("Table not found for url:", url)
        else:
            print("Div with class 'tx-ciuniversity' not found for url:", url)
    else:
        print("Failed to retrieve the webpage for url:", url, "Status code:", response.status_code)
    
    # Return the list of course links
    return modules
    
def get_courses(url, host="https://hpi.de/"):
    """
    Retrieves all master's degree links from the given url.
    """
    courses = []

    # Send a GET request to the given url
    response = requests.get(url)

    # Check if the response status code is 200 (OK)
    if response.status_code == 200:
        # Parse the HTML content of the response using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the div with class "csc-textpic-text"
        textpic_div = soup.find('div', class_='csc-textpic-text')
        
        if textpic_div:
            # Find all links in the div
            links = textpic_div.find_all('a')
            
            for link in links:
                href = link.get('href')

                if href.startswith("http"):
                    # add the course to the list of courses
                    courses.append(href)
                else:
                    # add the course to the list of courses
                    courses.append(host + href)
                
        else:
            print(f"Div with class 'csc-textpic-text' not found for url: {url}.")
    else:
        print(f"Failed to retrieve the webpage {url}. Status code:", response.status_code)
    
    return courses
