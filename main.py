from bs4 import BeautifulSoup
import math

# https://stackoverflow.com/questions/8595973/truncate-to-three-decimals-in-python
def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

StoryPoints = "series-field_customfield_10002-value"
StoryPointsDecrease = "series-field_customfield_10002-dec"
StoryPointsIncrease = "series-field_customfield_10002-inc"
ReportTemplate = '''
Started sprint with {} points
Finished sprint with {} points
We had {}% story point completion this sprint.
{} points were completed throughout the sprint.

{} points were added into the sprint after the beginning of the sprint.
{} points were removed from the sprint.
As a result of scope changes on tickets (pointed tickets increasing or decreasing in value), there were {} points added to the sprint.

If we were to take all scope changes and taking total points completed over it, we get {}% completed.

Any difference between actual points completed and beginning points can be attributed to scope changes in the middle of the sprint.

'''

def soupifyBurndown():
    with open('burndown.html') as f:
        burndownHtml = f.read()
    soup = BeautifulSoup(burndownHtml, 'html.parser')
    return soup

def getSprintStart(allTrs):
    for tr in allTrs:
        if tr.find(headers="series-event-type") and tr.find(headers="series-event-type").get_text() == "Sprint start":
            return int(tr.find(headers=StoryPoints).get_text())
    print("missing a sprint start value")
    return 0

# make a guess since points rolling over apparently counts as "being added to the sprint".
def getSprintStartWithHeuristic(allTrs):
    startValue = 0
    for i, tr in enumerate(allTrs):
        if tr.find(headers="series-event-type") and tr.find(headers="series-event-type").get_text() == "Sprint start":
            startIdx = i
            startValue = int(tr.find(headers=StoryPoints).get_text())
    currIdx = startIdx + 1
    tr = allTrs[currIdx]
    while tr.find(headers="series-event-detail") and tr.find(headers="series-event-detail").get_text() == "Issue added to sprint":
        if tr.find(headers=StoryPoints) and tr.find(headers=StoryPoints).get_text().isdigit():
            startValue = int(tr.find(headers=StoryPoints).get_text())
        currIdx += 1
        tr = allTrs[currIdx]
    return [startValue, currIdx]

def getSprintEnd(allTrs):
    # maybe there's a "Sprint ended" column.
    for i in range(len(allTrs) -1, -1, -1):
        tr = allTrs[i]
        if tr.find(headers="series-event-type") and 'Sprint ended by' in tr.find(headers="series-event-type").get_text():
            allSps = tr.find(headers=StoryPoints)
            return int(allSps.find_all('div')[-1].get_text())

    # iterate from the last tr and try and find the "final" burndown value if sprint wasn't ended
    for i in range(len(allTrs) -1, -1, -1):
        tr = allTrs[i]
        if tr.find(headers=StoryPoints) and tr.find(headers=StoryPoints).get_text().isdigit():
            return int(tr.find(headers=StoryPoints).get_text())
    print("missing a sprint end value")
    return 0

def getPointsCompleted(allTrs):
    totalCompleted = 0
    for tr in allTrs:
        if tr.find(headers="series-event-detail") and tr.find(headers="series-event-detail").get_text() == "Issue completed":
            if tr.find(headers=StoryPointsDecrease) and tr.find(headers=StoryPointsDecrease).get_text().isdigit():
                totalCompleted += int(tr.find(headers=StoryPointsDecrease).get_text())
                
    return totalCompleted

def getPointsAdded(allTrs, idx = 0):
    totalAdded = 0
    for tr in allTrs[idx:]:
        if tr.find(headers="series-event-detail") and tr.find(headers="series-event-detail").get_text() == "Issue added to sprint":
            if tr.find(headers=StoryPointsIncrease) and tr.find(headers=StoryPointsIncrease).get_text().isdigit():
                totalAdded += int(tr.find(headers=StoryPointsIncrease).get_text())
                
    return totalAdded

def getPointsRemoved(allTrs):
    totalRemoved = 0
    for tr in allTrs:
        if tr.find(headers="series-event-detail") and tr.find(headers="series-event-detail").get_text() == "Issue removed from sprint":
            if tr.find(headers=StoryPointsDecrease) and tr.find(headers=StoryPointsDecrease).get_text().isdigit():
                totalRemoved += int(tr.find(headers=StoryPointsDecrease).get_text())
                
    return totalRemoved

def getScopeChanges(allTrs):
    totalScopeChange = 0
    for tr in allTrs:
        if tr.find(headers="series-event-type") and tr.find(headers="series-event-type").get_text() == "Scope change":
             if tr.find(headers="series-event-detail") and 'Estimate' in tr.find(headers="series-event-detail").get_text():
                if tr.find(headers=StoryPointsDecrease) and tr.find(headers=StoryPointsDecrease).get_text().isdigit():
                    totalScopeChange -= int(tr.find(headers=StoryPointsDecrease).get_text())
                elif tr.find(headers=StoryPointsIncrease) and tr.find(headers=StoryPointsIncrease).get_text().isdigit():
                    totalScopeChange += int(tr.find(headers=StoryPointsIncrease).get_text())
                
    return totalScopeChange

def main():
    soup = soupifyBurndown()
    allTr = soup.find_all('tr')
    startingStoryPoints = getSprintStart(allTr)
    endingStoryPoints = getSprintEnd(allTr)
    totalCompleted = getPointsCompleted(allTr)
    pointsAdded = getPointsAdded(allTr)
    pointsRemoved = getPointsRemoved(allTr)
    scopeChanges = getScopeChanges(allTr)

    totalPoints = startingStoryPoints - pointsRemoved + pointsAdded + scopeChanges


    print('Without applying heuristic:', ReportTemplate.format(
        startingStoryPoints,
        endingStoryPoints,
        truncate((startingStoryPoints - endingStoryPoints)/startingStoryPoints, 2) * 100,
        totalCompleted,
        pointsAdded,
        pointsRemoved,
        scopeChanges,
        truncate(totalCompleted/totalPoints, 2)*100,
    ))

    heuristicStart, endIdx = getSprintStartWithHeuristic(allTr)
    pointsAdded = getPointsAdded(allTr, endIdx)
    print('If applying heuristic:', ReportTemplate.format(
        heuristicStart,
        endingStoryPoints,
        truncate((heuristicStart - endingStoryPoints)/heuristicStart, 2) * 100,
        totalCompleted,
        pointsAdded,
        pointsRemoved,
        scopeChanges,
        truncate(totalCompleted/totalPoints, 2)*100,
    ))

if __name__ == '__main__':
    main()