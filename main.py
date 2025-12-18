from dotenv import load_dotenv
from discord.commands import Option
from discord.ext import tasks
import discord
import datetime
import os
import json
import TAssist
import TA_Discord
import SCHOOL_Discord

print("starting...")
# Set to false in production
DEBUG = False

# Initialization shenanigans
load_dotenv()
TOKEN = os.getenv('DISCORD_TEST_TOKEN') if DEBUG else os.getenv(
    'DISCORD_TOKEN')
PREFIX = ">"

client = discord.Bot(command_prefix=PREFIX)

guilds = TA_Discord.GUILDS
color = TA_Discord.COLOR


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game(f'Find your grades and lookup clubs!'))

    TA_Discord.bootup()

    print("\n#### Ready ####")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if "bear" in message.content.lower():
        myid = '<@451860654500872192>'
        await message.channel.send(f"{myid}")


@client.slash_command(guilds=TA_Discord.GUILDS)
async def test(ctx, bruh: str):
    print("eugh")
    await ctx.respond(bruh)

ta = discord.SlashCommandGroup("ta", "Get data from Teach Assist")


@ta.command(description="Check status of Teach Assist server and API", guilds=guilds)
async def status(ctx):
    # Read from users.json
    with open(TA_Discord.ROOT + 'users.json', 'r') as users:
        credentials = json.load(users)

    # Check if logged in
    if str(ctx.author.id) not in credentials:
        connection_msg, connected, connection_status = TAssist.ping_server()
        await ctx.respond(f"**[{connection_status}]** {connection_msg} {'✅' if connected else '❌'}")
        await ctx.send(f'For a more detailed status, please login using **>ta login**')
        return False
    else:
        # Get user credentials
        credentials = credentials[str(ctx.author.id)]
        username = credentials[0]
        password = credentials[1]

        # Create teach assist account
        account = TAssist.Student(username, password)

        # Check if can connect with TA
        connection_msg, connected, connection_status = account.fetch_data()
        await ctx.respond(f"**[{connection_status}]** {connection_msg} {'✅' if connected else '❌'}")


@ta.command(description="Log into Teach Assist", guilds=guilds)
async def login(ctx, studentnumber: Option(str, "Enter your TA student number", required=True, default=False), password: Option(str, "Enter your TA password", required=True, default=False)):
    # Read from users.json
    with open(TA_Discord.ROOT + 'users.json', 'r') as users:
        signed = json.load(users)

        # Remove user from list if present
        if ctx.author.id in signed.keys():
            signed.pop(str(ctx.author.id))
            TA_Discord.outta_cache(ctx)

        # Put user input in a dict and update previous json data
        entry = {str(ctx.author.id): [studentnumber, password]}
        signed.update(entry)

        # Test if can connect with TA
        account = TAssist.Student(studentnumber, password)
        connection_msg, connected, connection_status = account.fetch_data()
        if connected:
            # Add to client cache
            TA_Discord.into_cache(ctx, account)
            with open(TA_Discord.ROOT + "users.json", "w") as users:
                json.dump(signed, users)
        elif connection_status == 500 or connection_status == 503:
            # Add to queue
            print("Into queue...")
            TA_Discord.queue_peek()
            TA_Discord.into_queue(ctx, studentnumber, password)

        await ctx.respond(f"[{connection_status}] {connection_msg}")
        # Send fail or success message


@tasks.loop(minutes=5)
async def server_status():
    if (TAssist.ping_server())[1]:
        await client.change_presence(status=discord.Status.online, activity=discord.Game(f'Teach Assist API is up ✅'))
    else:
        await client.change_presence(status=discord.Status.online, activity=discord.Game(f'Teach Assist API is down ❌'))


@tasks.loop(minutes=60)
async def check_queue():
    print("Trying queue")
    if not len(TA_Discord.QUEUED_CLIENTS):
        print("Queue is empty")
        return True
    for user, creds in TA_Discord.QUEUED_CLIENTS:
        username = creds[0]
        password = creds[1]
        ctx = creds[2]

        account = TAssist.Student(username, password)
        connection_msg, connected, connection_status = account.fetch_data()

        print(connection_msg, '[', str(connection_status), ']')
        if connection_status == 500 or connection_status == 503:
            break
        elif connected:
            # Add to cache
            TA_Discord.into_cache(ctx, account)

            # Add to users
            with open(TA_Discord.ROOT + 'users.json', 'r') as users:
                signed = json.load(users)
                signed.update({user: [username, password]})
                with open(TA_Discord.ROOT + "users.json", "w") as users:
                    json.dump(signed, users)

            # Message User
            user = client.get_user(int(user))
            await user.send("Succesfully connected to Teach Assist!")


@ta.command(description="Sign out of Teach Assist", guilds=guilds)
async def disconnect(ctx):
    # Read from users.json
    with open(TA_Discord.ROOT + 'users.json', 'r') as users:
        signed = json.load(users)

        # Remove user
        if str(ctx.author.id) in signed:
            TA_Discord.outta_cache(ctx)
            signed.pop(str(ctx.author.id))
            with open(TA_Discord.ROOT + "users.json", "w") as users:
                json.dump(signed, users)
            await ctx.respond("Succesfully disconnected your TA account from this discord bot!")
        else:
            await ctx.respond("An error has occured: You are not already logged in")


@ta.command(description="Sends Teach Assist data", guilds=guilds)
async def view(ctx, course: Option(str, "Enter a course code for a class", required=False, default=None), assignment: Option(str, "Enter an assignment", required=False, default=None)):
    # Read from users.json
    with open(TA_Discord.ROOT + 'users.json', 'r') as users:
        credentials = json.load(users)

    # Check if logged in
    if str(ctx.author.id) not in credentials:
        await ctx.respond(f'Unidentified user. Please login using **/ta login**')
        return False

    else:

        # Get credentials
        credentials = credentials[str(ctx.author.id)]
        username = credentials[0]
        password = credentials[1]

        # Create teach assist account
        account = TAssist.Student(username, password)

        # Check if can connect with TA
        connection_msg, connected, connection_status = account.fetch_data()
        if not connected:
            cached_client = TA_Discord.CACHED_CLIENTS.get(str(ctx.author.id))
            if cached_client:
                if (cached_client[0].password == password) and (cached_client[0].username == username):
                    # Get cached account object
                    account = TA_Discord.CACHED_CLIENTS[str(ctx.author.id)][0]

                    # Send fallback message
                    last = datetime.datetime.now(
                    ) - TA_Discord.CACHED_CLIENTS[str(ctx.author.id)][1]

                    if last.days > 0:
                        text = f"{last.days} days ago."
                    elif last.days <= 0 and last.seconds > 60:
                        text = f"{round(last.seconds / 60, 2)} minutes and {last.seconds % 60} seconds ago."
                    else:
                        text = f"{last.seconds} seconds ago."
                    await ctx.author.send(f"Using fallback from **{text}**")
            else:
                await ctx.respond(connection_msg)
                return True
        else:
            # Replace or add new entry to cache
            TA_Discord.into_cache(ctx, account)

        if course is None:
            # General overview embed
            General_Embed = TA_Discord.general_view_embed(account, color)
            await ctx.respond(embed=General_Embed)
            return True

        # Get class if it exists
        user_course = account.has_class(course)

        # Quit if class doesnt exist exists
        if not user_course:
            # Drop down for course choice
            options = [discord.SelectOption(label=c.code, emoji=c.emoji, description="Room: " + c.room)
                       for c in account.courses if (c.overall_mark is not None)]

            if len(options) <= 0:
                await ctx.respond(f"**Error**. Cant find any class data")
            course_select = discord.ui.Select(
                placeholder="Choose a course",
                options=options
            )

            async def course_select_callback(interaction):
                # Return class view for that course
                found_class = account.has_class(course_select.values[0])
                class_file, class_embed, class_view = TA_Discord.class_view_wrapper(
                    found_class, color)
                await interaction.response.send_message(file=class_file, embed=class_embed, view=class_view)

            async def course_assignment_select_callback(interaction):
                found_class = account.has_class(course_select.values[0])
                success, msg, view = TA_Discord.assignment_view_wrapper(
                    found_class.has_assignment(assignment), found_class, assignment, course, color)
                if success:
                    interaction.response.send_message(view=view, embed=msg)
                else:
                    interaction.response.send_message(msg)

            if not assignment:
                course_select.callback = course_select_callback
            else:
                course_select.callback = course_assignment_select_callback

            course_view = discord.ui.View(course_select)

            await ctx.respond(f"**Error**. No such course name, code, block number in your account named: *{course}*\nDid you mean: ", view=course_view)
            return True

        # Get assignment if it exists
        user_assignment = user_course.has_assignment(assignment)

        if course and not assignment:
            class_file, class_embed, class_view = TA_Discord.class_view_wrapper(
                user_course, color)
            await ctx.respond(file=class_file, embed=class_embed, view=class_view)
            return True

        elif course and assignment:
            success, msg, view = TA_Discord.assignment_view_wrapper(
                user_assignment, user_course, assignment, course, color)
            if success:
                await ctx.respond(embed=msg, view=view)
            else:
                await ctx.respond(msg)
            return True


@ta.command(description="Sends Teach Assist data from prewritten file", guilds=guilds)
async def test_visuals(ctx, course: Option(str, "Enter a course code or block number for a class", required=False, default=None), assignment: Option(str, "Enter an assignment", required=False, default=None)):

    account = TAssist.TEST_USER

    if course is None:
        # General overview embed
        General_Embed = TA_Discord.general_view_embed(account, color)
        await ctx.respond(embed=General_Embed)
        return True

    # Get class if it exists
    user_course = account.has_class(course)

    # Quit if class doesnt exist exists
    if not user_course:
        # Drop down for course choice
        course_select = discord.ui.Select(
            placeholder="Choose a course",
            options=[discord.SelectOption(label=c.code, emoji=c.emoji, description="Room: " + c.room)
                     for c in account.courses if (c.overall_mark is not None)]
        )

        async def course_select_callback(interaction):
            # Return class view for that course
            found_class = account.has_class(course_select.values[0])
            class_file, class_embed, class_view = TA_Discord.class_view_wrapper(
                found_class, color)
            await interaction.response.send_message(file=class_file, embed=class_embed, view=class_view)

        async def course_assignment_select_callback(interaction):
            found_class = account.has_class(course_select.values[0])
            success, msg, view = TA_Discord.assignment_view_wrapper(
                found_class.has_assignment(assignment), found_class, assignment, course, color)
            if success:
                interaction.response.send_message(view=view, embed=msg)
            else:
                interaction.response.send_message(msg)

        if not assignment:
            course_select.callback = course_select_callback
        else:
            course_select.callback = course_assignment_select_callback

        course_view = discord.ui.View(course_select)

        await ctx.respond(f"**Error**. No such course name, code, block number in your account named: *{course}*\nDid you mean: ", view=course_view)
        return True

    # Get assignment if it exists
    user_assignment = user_course.has_assignment(assignment)

    if course and not assignment:
        class_file, class_embed, class_view = TA_Discord.class_view_wrapper(
            user_course, color)
        await ctx.respond(file=class_file, embed=class_embed, view=class_view)
        return True

    elif course and assignment:
        success, msg, view = TA_Discord.assignment_view_wrapper(
            user_assignment, user_course, assignment, course, color)
        if success:
            await ctx.respond(embed=msg, view=view)
        else:
            await ctx.respond(msg)
        return True


info = discord.SlashCommandGroup("info", "Get School Info")

@info.command(description="Find out more about YRDSB schools", guilds=guilds)
async def schools(ctx):
    school_select = discord.ui.Select(
        placeholder="Choose a school",
        options=[discord.SelectOption(label=s.name.upper(
        ), emoji="🏫", description=s.fullname) for s in SCHOOL_Discord.school_list()]
    )

    async def school_select_callback(interaction):
        school = SCHOOL_Discord.school_lookup(school_select.values[0])
        embed = SCHOOL_Discord.school_embed(school)
        await interaction.response.send_message(embed=embed)
    school_select.callback = school_select_callback
    school_view = discord.ui.View(school_select)

    await ctx.respond(f"Pick a school you'd like to inspect from the dropdown:", view=school_view)


@info.command(description="Find out more about the clubs at YRDSB schools", guilds=guilds)
async def clubs(ctx, name: Option(str, "Enter a school name or prefix (ex: BHSS)", required=True, default="bhss")):
    school = SCHOOL_Discord.school_lookup(name)
    if not school:
        await ctx.respond(f"No data avaialable for/ could not find school: **{name}**")
        return False
    clubs, lookup = SCHOOL_Discord.club_list(school)

    club_select = discord.ui.Select(
        placeholder="Choose a club(s)",
        min_values=1,
        max_values=len(clubs) if len(clubs) < 25 else 25,
        options=[discord.SelectOption(
            label=club.name, emoji=club.emoji, description=club.description[:100]) for club in clubs[:25]]
    )

    async def club_select_callback(interaction):
        await interaction.response.send_message("Here's your info...")
        for clubname in club_select.values:
            club = lookup.get(clubname)
            embed, view = SCHOOL_Discord.club_embed(club)

            await ctx.send(embed=embed, view=view)

    club_select.callback = club_select_callback
    course_view = discord.ui.View(club_select)
    await ctx.respond(f"{school.name.upper()} Test ")
    print(club_select.options)
    print(club_select.values)


    print(course_view)
    await ctx.respond(f"Here is a list of clubs at {school.name.upper()} (more to be added soon): ", view=course_view)

check_queue.start()
server_status.start()

client.add_application_command(ta)
client.add_application_command(info)
client.run(TOKEN)
