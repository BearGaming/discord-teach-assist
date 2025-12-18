# Wrapper for graph generation code
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager
import matplotlib.patheffects as pe
from scipy.interpolate import make_interp_spline
import numpy.ma as ma

import math

class TA_Graph:
    def __init__(self, plot, output, delimeter, name, type):
        self.output = output
        self.delimeter = delimeter
        self.type =  type
        self.plot = plot
        
        self.name = name.replace("/","-")

        self.filename = f'{self.delimeter}_{self.name}.{self.type}'
        self.directory = f'{output}/{self.filename}'
        self.discord_attatched = f'attachment://{self.filename}'

        self.plot.savefig(self.directory, bbox_inches='tight')

def mark_graph(output, mark, course_code):
    plt.figure().clear()
    # Prettify mark given
    if mark is None:
        mark = 0
        mark_display = '-NA-'
    else:
        mark = float(mark)
        mark = round(mark, 1)
        mark_display = str(mark) + '%'

    # Graph size
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'projection':'polar'})
    plt.ylim(-3, 3)

    # Set values
    bar_percentage = (mark * math.pi *2)/ 100
    bar_value = ((90 * math.pi *2)/ 360)
    bar_height = 1
    bar_color = '#00ff62'

    # Make Bars
    ax.barh(1, bar_percentage, bar_height, bar_value, color=bar_color) 
    plt.text(0, -3, mark_display, ha='center', va='center', fontsize=42)

    # Clear tick marks
    plt.xticks([])
    plt.yticks([])
    ax.spines.clear()

    # Save the graph
    return TA_Graph(fig, output, 'ring', course_code, 'png')

def prep_grade_data(data, categories, suffix=""):
    # Add a suffix to data if provided
    ad_fix = lambda num: (str(num) + suffix) if suffix else (num) 

    # Prepare lists to be populated
    weighting = []
    course_weighting = []
    student_achievement = []

    # Bring data from weight_table into lists
    for row in categories.values():
        # Get and round and store data
        weight_data = ad_fix(round(data[row]['W'], 2))
        weighting.append(weight_data)

        course_weight_data = ad_fix(round(data[row]['CW'], 2))
        course_weighting.append(course_weight_data)

        student_achievement_data = ad_fix(round(data[row]['SA'], 2))
        student_achievement.append(student_achievement_data)
    
    return weighting, course_weighting, student_achievement

def grade_rose_chart(output, course_code, data, categories, colors):
        plt.figure().clear()
        weighting, course_weighting, student_achievement = prep_grade_data(data, categories)

        # Merge info from weight table for the polar chart
        polar_angles = [0]
        polar_positions = [0]

        # Tweak data to suit the graph
        for angle in course_weighting:
            # Rescale angle data to fit graph
            rescaled_angle = math.radians(angle / 100 * 360)
            polar_angles.append(rescaled_angle)

            # Find and set position for next slice
            new_slice_position = polar_positions[-1] + ((polar_angles[-1] / 2) + (polar_angles[-2] / 2))
            polar_positions.append(new_slice_position)

        # Covert to np arrays
        polar_radii = np.array(student_achievement)
        polar_positions = np.array(polar_positions[1:])
        polar_angles = np.array(polar_angles[1:])

        # Make polar chart
        polar = plt.subplot(projection='polar')
        polar_ax = polar.bar(polar_positions, polar_radii, polar_angles, color=colors, edgecolor='black', bottom=0.0, alpha=0.5)

        # Add chart labels
        for count, bar in enumerate(polar_ax):
            if bar.get_height() > 0:
                text = list(categories.keys())[count]
                polar.text(polar_positions[count], 50, text, ha='center', va='bottom')

        # Hide axes ticks
        polar.grid(False)
        polar.set_xticks([])
        polar.set_yticks([])

        # Save the polar
        return TA_Graph(plt, output, 'polar', course_code, 'png')


def grade_table_chart(output, course_code, data, categories, columns, colors):
    plt.figure().clear()
    # Merge info from weight table into table text with '%sign' at the end
    weighting, course_weighting, student_achievement = prep_grade_data(data, categories, suffix="%")
    table_text = list(zip(list(categories.keys()), weighting, course_weighting, student_achievement))

    # Make table
    table = plt.subplot()
    table_ax = table.table(cellText=table_text,
                        colLabels=columns,
                        cellColours=[[color for n in range(len(columns))] for color in colors],
                        colLoc='center',
                        loc='top',
                        bbox=[0, 0.2, 1.2, 0.6]
                        )

    # Make first row bolded
    for (row, col), cell in table_ax.get_celld().items():
        if (row == 0):
            cell.set_text_props(fontproperties=matplotlib.font_manager.FontProperties(weight='bold'))

    # Table font size
    table_ax.set_fontsize(14)
    table_ax.scale(1.5, 1.5)

    # Hide axis
    plt.tight_layout()
    plt.axis('off')

    # Save the table
    return TA_Graph(plt, output, 'table', course_code, 'png')

def course_trendline(output, assignments, course_code, categories, color):
    plt.figure().clear()

    # x-axis
    x = np.array([i for i in range(len(assignments))])

    data = []
    for assignment in assignments:
        avg = assignment.avg if assignment.avg > 0 else sum(data)/len(data)
        total = sum(data) + avg
        total /= len(data) + 1
        
        data.append(total)

    y = np.array(data)
    # line of best fit
    m, b = np.polyfit(x, y, 1)
    
    # smooth line
    X_Y_Spline = make_interp_spline(x, y)
    X_ = np.linspace(x.min(), x.max(), 500)
    Y_ = X_Y_Spline(X_)
    
    # Plotting the Graph
    plt.plot(X_, Y_,"-k", label="Average over time")
    plt.plot(x, m*x + b,"--r", label="Trendline")
    plt.legend(loc="upper right")

    # Set y axis scale to 0-100 and remove x-ticks
    plt.ylim((0,100))
    plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False) 

    plt.title(f"Analysis for {course_code}")
    plt.xlabel("Assignments")
    plt.ylabel("Percent (%)")

    plt.grid(True)

    # Save the table
    return TA_Graph(plt, output, 'trend', course_code, 'png')

def assignment_bars(output, assignment, categories, colors):
    plt.figure().clear()
    plt.figure(figsize=(8, 6))

    # Disable axes from rendering
    ax1 = plt.axes(frameon=False)
    ax1.get_xaxis().tick_bottom()
    ax1.axes.get_yaxis().set_visible(False)
    ax1.set_ylim([0, 100])

    # creating the dataset
    values = [assignment.KU.percent, assignment.T.percent, assignment.C.percent, assignment.A.percent]
    colors = colors[:len(values)]
    category = list(categories.values())[:len(values)]
    
    # creating the bar plot
    bar = plt.bar(category, values, color = colors, width = 0.4, edgecolor="black")

    # Add text above bar
    for count, rect in enumerate(bar):
        height = rect.get_height()
        plt.text(rect.get_x() + rect.get_width() / 2.0, height, (str(values[count]) + "%" if values[count] > 0 else "-NA-"), ha='center', va='bottom')
    
    plt.xlabel("Categories")
    plt.title(f"Marks for {assignment.name} ({assignment.course.code})", pad=20)
    return TA_Graph(plt, output, 'marks', assignment.name, 'png') 