"""IdleMiner: Story Mode event system"""
import json
import time


story = json.load(open("data/storyline.json"))


def segmentparser(segment: dict, alex):  # TODO
    """parses story segment?"""

    if "description" in segment:
        for i in segment["description"]:
            print(i)
            time.sleep(1)

    if "triggers" in segment:
        for i in segment["triggers"]:
            # execaction(i)
            print(i)

    if "conditional" in segment:
        for i in segment["conditional"].keys():
            print(i)


def move(area, place, alex):
    """calls event"""
    segmentparser(story[area][place], alex)


def call(event, alex):
    segmentparser(story[event], alex)
