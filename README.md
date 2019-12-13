# Jira Parser

This is something I'm writing for work to parse the jira burndown html.

Require python3 and BeautifulSoup which can be installed using `pip install beautifulsoup4`.

# How to use
Inspect the page and take the body of the HTML using the inspector. Save it to burndown.html.

(I wasn't able to anything useful via the network tab). Perhaps the JIRA api has something better, but I don't have access to that at work.

Run `python main.py` or `python3 main.py` depending on your alias for python3.