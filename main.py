# coding=utf-8
from utils.perpetual_agent import PerpetualAgent


# https://github.com/stevenic/alphawave-py
# for generic function calls

# https://github.com/1rgs/jsonformer
# for generic structuring of data

if __name__ == "__main__":
    # request = "Given a list of integers, return the sum of all even numbers."
    request = "What is today's weather in Bamberg, Germany."
    # request = "Crawl the Google weather site for the current weather conditions in Bamberg, Germany."
    # request = "What is the composition of the core of the moon?"
    # request = "What is the abaddon of the third house?"
    # request = "Create a file containing a Markdown list of all planets in the solar system and their moons as sub lists."
    # request = "How do you remove ticks from a tadpole?"
    # request = "Write a Python function that returns the sum of the first 567 prime numbers that contain the digit 8."
    # request = "Generate a file called 'moon_core.md' that contains a structural analysis of the chemical composition of the core of the moon in markdown syntax."
    # request = "Research five diverse positions on the possibility of artificial consciousness and save them as structured summary in a markdown file."

    print(request)
    print()
    perpetual = PerpetualAgent()
    response = perpetual.respond(request)
    print(response)
