import discord
import datetime
import os
import json
import SCHOOL
import SCHOOL_Globals
from SCHOOL_Globals import ROOT

def school_list():
    schools = []
    for school in SCHOOL_Globals.school_urls.keys():
        schools.append(SCHOOL.School(school))
        print("Added: " + schools[-1].fullname)
    return schools

def school_lookup(name):
    name = name.lower()
    schools = school_list()

    for school in schools:
        if (name in school.fullname) or (name in school.name) or (name in school.url): return school
    return False

def club_list(school):
    with open(ROOT + "clubs/" + school.name + ".json", 'r') as f:
        data = json.load(f)

        clubs = []
        lookup = {}
        for club in data:
            clubs.append(SCHOOL.Club(club, school.url))
            lookup[clubs[-1].name] = clubs[-1]

    return clubs, lookup

def club_embed(club):
    embed=discord.Embed(title=f"{club.emoji} {club.name}", description=club.description, color=SCHOOL_Globals.COLOR)

    how_to, events = club.how_to, club.events
    if how_to: embed.add_field(name="How to join:", value=how_to, inline=False)
    if events: embed.add_field(name="Upcoming events:", value=events, inline=False)

    link_button = discord.ui.Button(label="Club Website", style=discord.ButtonStyle.link, url=club.url)
    club_view = discord.ui.View(link_button)

    return embed, club_view

def school_embed(school):
    embed=discord.Embed(title=f"🏫 {school.name.upper()}", url=school.url, description=f"{school.fullname} is in the YRDSB and located at {school.address}.", color=SCHOOL_Globals.COLOR)
    embed.set_thumbnail(url="https://is2-ssl.mzstatic.com/image/thumb/Purple112/v4/73/1d/ab/731dab1b-747b-1a71-c99c-c1a160f4afdf/AppIcon-0-0-1x_U007emarketing-0-0-0-10-0-0-sRGB-0-0-0-GLES2_U002c0-512MB-85-220-0-0.png/512x512bb.jpg")
    embed.add_field(name="📞 Phone number", value=school.phone, inline=True)
    embed.add_field(name="📧 E-mail", value=school.email, inline=True)
    embed.set_footer(text="Use /info clubs to get a list of clubs at a particular school")
    return embed