"""IdleMiner: Story Mode event system"""
import json


story: dict[str: list] = json.load(open("data/story.json"))


def call(event):
    for i in story[event]:
        print(i)
