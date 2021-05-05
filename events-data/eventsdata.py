from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import sys

class EventsData:
    # eventbrite_apikey = config('EVENTBRITE_API')
    eventbrite_apikey = "ZDYPJLN3GKLRZTOWJNS2"

    def __init__(self):
        self.eventbrite_url = "https://www.eventbrite.com/d/online"

    def get_eventbrite_page_numbers(self, soup):
        nav = soup.find("footer").find("div", class_="undefined paginator__link eds-l-pad-top-2 eds-text-weight--heavy")
        pages = nav.find("a").get_text()
        return int(pages)
    
    def get_eventbrite_events(self, hashtag, date):
        events = []
        base_url = "{url}/events--{date}/%23{hashtag}/?page=".format(url=self.eventbrite_url, date=date, hashtag=hashtag)

        max_page = sys.maxsize
        current_page = 1
        while current_page <= max_page:
            print("CURRENT PAGE", current_page, "MAX PAGE", max_page)
            # URL = base_url + str(current_page)
            URL = "https://www.eventbrite.com/d/online/events--today/%23sustainability/?page=3"
            print("URL", URL)
            page = requests.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")
            if (max_page == sys.maxsize):
                max_page = self.get_eventbrite_page_numbers(soup)

            parent = soup.find("ul", class_="search-main-content__events-list")
            event_list = parent.find_all("li")
            for event in event_list:
                event = event.find_all("div", class_="eds-event-card-content__primary-content")
                # print(event)
                if len(event) > 0:
                    event = event[0]
                    children = list(event.children)
                    title = children[0].find("h3").get_text()

                    # TODO: find less hacky way of doing this
                    title = title[:len(title)//2]
                    # print(title)
                    link = children[0]["href"]
                    date = children[1].get_text()
                    event_obj = {"event_name": title, "event_date": date, "link": link}
                    if event_obj not in events:
                        events.append(event_obj)
            current_page += 1
        with open("test-data/eventbrite_events.json", "w") as f:
            json.dump(events, f, indent=2)


if __name__ == "__main__":
    events = EventsData()
    events.get_eventbrite_events("sustainability", "today")
