import discord
import datetime
import json
import os
import TAssist
import TA_Graphs
import TA_Globals
from TA_Globals import ROOT

CACHED_CLIENTS = {}
QUEUED_CLIENTS = {}
GUILDS = [779179469444481045, 883104459285233694, 719414209812889675]
COLOR = 0x00ff62

CACHE_PATH = ROOT + 'json_cache/'

def cache_peek():
    print("Cache: " + str([key for key in CACHED_CLIENTS.keys()]))

def queue_peek():
    print("Queue: " + str([key for key in QUEUED_CLIENTS.keys()]))

def outta_cache(ctx):
    CACHED_CLIENTS.pop(str(ctx.author.id))
    os.remove(CACHE_PATH + str(ctx.author.id) + '.json')
    cache_peek()

def into_cache(ctx, account):
    CACHED_CLIENTS[str(ctx.author.id)] = account, datetime.datetime.now()
    account.save_json(CACHE_PATH, str(ctx.author.id))
    cache_peek()

def into_queue(ctx, studentnumber, password):
    if not QUEUED_CLIENTS.get(str(ctx.author.id), False):
        QUEUED_CLIENTS[str(ctx.author.id)] = studentnumber, password, ctx
    queue_peek()

def outta_queue(ctx):
    QUEUED_CLIENTS.pop(str(ctx.author.id))
    queue_peek()

def bootup():
    # Ping TA
    print("Pinging TA...")
    ping_msg, ping_bool, ping_status = TAssist.ping_server()
    print(ping_msg + ' ' + str(ping_status))

    # Read from json into cache
    cache_peek()
    print("Loading into cache...")
    for filename in os.listdir(CACHE_PATH):
        if filename.endswith('.json'):
            # The json file
            file = os.path.join(CACHE_PATH, filename)
            with open(file, 'r') as f:
                # Json filename is discord user id
                discord_id = filename[:-5]
                with open(ROOT + 'users.json', 'r') as users:
                    # Get user creds if they exist on file
                    creds = json.load(users).get(discord_id, False)
                    if creds:
                        # Make account with creds
                        account = TAssist.Student(creds[0], creds[1])
                        # Use saved json data if cant connect to TA
                        if not ping_bool: account.read_json(file)
                        # Add account to cache
                        CACHED_CLIENTS[discord_id] = account, datetime.datetime.now()
    cache_peek()

## EMBEDS/VIEWS ##
def set_graph(embed, graph):
    file = discord.File(graph.directory, filename=graph.filename) 
    embed.set_thumbnail(url=f'attachment://{graph.filename}')
    return file

def send_graph(embed, graph):
    file = discord.File(graph.directory, filename=graph.filename)
    embed.set_image(url=f"attachment://{graph.filename}")
    return file

def general_view_embed(account, COLOR):
    embed=discord.Embed(title="General overview", description="See the details for a specific class by doing '>TA' followed by your coursecode or block number", color=COLOR)
    embed.set_author(name="Teach Assist", url="https://ta.yrdsb.ca/yrdsb/")
    embed.set_thumbnail(url="https://cdn.freebiesupply.com/logos/large/2x/teachassist-1-logo-png-transparent.png")
    for course in account.courses:
        if course.overall_mark is not None: course_mark = str(round(course.overall_mark, 2)) + '%'
        else: course_mark = "-NA-"
        embed.add_field(name=course.code, value=f"Average: *{course_mark}*", inline=False)
    embed.set_footer(text=f"Your overall average is: {round(account.total_average, 2)}%")
    return embed

def class_view_embed(course, COLOR):

    embed_title = f"Block {course.block} - Room {course.room}"
    embed_description =f"Here is an overview for your class, {course.code}. This class **starts on**: *{course.start}* and **ends:** *{course.end}*. You have **{course.assign_len} assignments** shown below." 
    embed_author = course.code + course.emoji

    embed = discord.Embed(title=embed_title, description=embed_description, color=COLOR)
    embed.set_author(name=embed_author)
    file = set_graph(embed, TA_Graphs.mark_graph(ROOT + 'course_marks', course.overall_mark, course.code))

    for assignment in course.assignments:
        embed.add_field(name=f"{assignment.name}", value=f"Average: {round(assignment.avg, 2)}%", inline=False)

    embed.set_footer(text=f"You can view a specific assignment with '/TA view {course.code}', followed by an assignment name.")

    return embed, file

def assignment_view_embed(course, assignment, COLOR):
    embed_title = f"Class: {course.code}"
    if course.name is not None: embed_title += f"({course.name})"

    weight_description = []
    for category in TA_Globals.CATEGORIES.values():
        weight = assignment.marks[category].weight if assignment.marks[category].weight else "N/A"
        weight_description.append(f"\nThis assignment has a weight of **{weight}** for **{category}**")
    weight_description = ''.join(weight_description)

    embed_description = f"Feedback: {assignment.feedback if assignment.feedback is not None else 'None provided'}.\n{weight_description}"

    embed=discord.Embed(title=embed_title, description=embed_description, color=COLOR)
    embed.set_author(name=assignment.name)

    for category in TA_Globals.CATEGORIES.values():
        weight = assignment.marks[category].weight if assignment.marks[category].weight else "N/A"

        percent = assignment.marks[category].percent
        if not percent: break

        field_name = f"**{category if category != 'KU' else 'K/U'}** [ {percent}% ]"
        field_mark = f"Mark: {assignment.marks[category].score}/{assignment.marks[category].out_of}"
        field_weight = f"Weight: {weight}"

        embed.add_field(name=field_name, value=f"{field_mark}\n{field_weight}", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/740573460170014830/972977834811342848/image_5.png")
    embed.set_footer(text="Graphs coming soon")

    return embed

def class_view_wrapper(user_course, COLOR):
     # Generate tables
    rose_graph, table_graph = user_course.generate_grade_tables(ROOT + 'course_weights')
    trend_graph = user_course.get_trendline(ROOT + 'course_trends')

    async def rose_button_callback(interaction):
        await interaction.response.send_message(file=send_graph(class_embed, rose_graph))

    async def table_button_callback(interaction):
        await interaction.response.send_message(file=send_graph(class_embed, table_graph))

    async def trends_button_callback(interaction):
        await interaction.response.send_message(file=send_graph(class_embed, trend_graph))

    # Generate and send class embed
    class_embed, class_file = class_view_embed(user_course, COLOR)   

    rose_button = discord.ui.Button(label="Weight chart", style=discord.ButtonStyle.secondary)
    rose_button.callback = rose_button_callback
    table_button = discord.ui.Button(label="Weight table", style=discord.ButtonStyle.secondary)
    table_button.callback = table_button_callback
    trends_button = discord.ui.Button(label="Trendline", style=discord.ButtonStyle.primary)
    trends_button.callback = trends_button_callback

    class_view = discord.ui.View(rose_button, table_button, trends_button)

    return class_file, class_embed, class_view

def assignment_view_wrapper(user_assignment, user_course, assignment, course, COLOR):
    # Quit if assignment doesnt exist exists
    if not user_assignment:
        return False, f"**Error**. No such assignment: *{assignment}* in class: {course}", False
         
    # Send assignment embed
    Assignment_Embed = assignment_view_embed(user_course, user_assignment, COLOR)

    async def bar_button_callback(interaction):
        Assignment_Graph = TA_Graphs.assignment_bars(ROOT + 'assignment_marks', user_assignment, TA_Globals.CATEGORIES, TA_Globals.COLORS)
        file = send_graph(Assignment_Embed, Assignment_Graph)
        await interaction.response.send_message(file=file)

    # Generate and send class embed
    class_embed, class_file = class_view_embed(user_course, COLOR)   

    bar_button = discord.ui.Button(label="Bar Graph", style=discord.ButtonStyle.secondary)
    bar_button.callback = bar_button_callback

    assignment_view = discord.ui.View(bar_button)

    return True, Assignment_Embed, assignment_view 