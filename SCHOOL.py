import requests
from bs4 import BeautifulSoup
import SCHOOL_Globals

class Club:
    def __init__(self, data, home):
        self.name = data["name"]
        self.description = data["description"]

        # Return school website if no club website
        self.url = data.get("url", home)

        self.how_to = data.get("how_to", False)
        self.events = data.get("events", False)
        
        self.emoji = SCHOOL_Globals.club_emojis[ (data["emoji_id"]) ]

class School:
    def __init__(self, name):
        self.name = name

        self.url = SCHOOL_Globals.school_urls.get(self.name)
        self.page = requests.get(self.url)
        soup = BeautifulSoup(self.page.content, 'html.parser')

        self.fullname = soup.find_all('div', class_='YRDSBPageTitle')[0].get_text().strip()

        divs = soup.find_all('div')
        for div in divs:
            within = div.find_all('div')
            if within and within[0].get_text() == "Contact Information":
                self.address = div.find('a').get_text()
                
                content = within[2]
                for breaks in content.find_all("br"): breaks.replace_with("amongus")
                info = content.get_text().split("amongus")

                self.phone = info[0]
                self.email = info[2]