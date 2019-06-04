"""Command line interface of taskschedule"""

import time
import curses
import argparse
import datetime

from isodate import parse_duration

from taskschedule.schedule import Schedule
from taskschedule.scheduled_task import ScheduledTask


def draw(stdscr, refresh_rate=1, hide_empty=True, scheduled='today',
         completed=True, hide_projects=False):
    """Draw the schedule using curses."""
    schedule = Schedule()
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, 20, curses.COLOR_BLACK)
    curses.init_pair(2, 8, 0)  # Hours
    curses.init_pair(3, 20, 234)  # Alternating background
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Header
    curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Current hour
    curses.init_pair(6, 19, 234)  # Completed task - alternating background
    curses.init_pair(7, 19, 0)  # Completed task
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Active task
    curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_BLACK)  # Glyph
    curses.init_pair(10, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Active task
    curses.init_pair(11, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Overdue task

    previous_as_dict = []

    while True:
        max_y, max_x = stdscr.getmaxyx()

        schedule.load_tasks(scheduled=scheduled, completed=completed)

        as_dict = schedule.as_dict()

        # Clear the screen if lines have changed since last time
        if as_dict != previous_as_dict:
            stdscr.clear()
        previous_as_dict = as_dict

        # Determine offsets
        offsets = schedule.get_column_offsets()

        # Draw headers
        headers = ['', '', 'ID', 'Time', 'Project', 'Description']

        color = curses.color_pair(4) | curses.A_UNDERLINE
        stdscr.addstr(0, offsets[1], headers[2], color)
        stdscr.addstr(0, offsets[2], headers[3], color)
        stdscr.addstr(0, offsets[3], headers[4], color)

        if not hide_projects:
            stdscr.addstr(0, offsets[4], headers[5], color)

        # Draw schedule
        past_first_task = False
        alternate = True
        current_line = 1
        for i in range(24):
            tasks = as_dict[i]
            if not tasks:
                # Add empty line if between tasks or option is enabled
                if past_first_task or not hide_empty:
                    if alternate:
                        color = curses.color_pair(1)
                    else:
                        color = curses.color_pair(3)

                    # Fill line to screen length
                    stdscr.addstr(current_line, 5, ' ' * (max_x - 5), color)

                    # Draw hour, highlight current hour
                    current_hour = time.localtime().tm_hour
                    if i == current_hour:
                        stdscr.addstr(current_line, 0, str(i),
                                      curses.color_pair(5))
                    else:
                        stdscr.addstr(current_line, 0, str(i),
                                      curses.color_pair(2))

                    current_line += 1
                    alternate = not alternate

            for ii, task in enumerate(tasks):
                try:
                    next_task = tasks[ii + 1]
                except IndexError:
                    is_current_task = False
                else:
                    is_current_task = task.should_be_active(next_task)

                past_first_task = True
                if task.active:
                    color = curses.color_pair(8)
                elif is_current_task:
                    color = curses.color_pair(10)
                elif task.overdue() and not task.completed:
                    color = curses.color_pair(11)
                else:
                    if alternate:
                        if task.completed:
                            color = curses.color_pair(7)
                        else:
                            color = curses.color_pair(1)
                    else:
                        if task.completed:
                            color = curses.color_pair(6)
                        else:
                            color = curses.color_pair(3)

                # Only draw hour once for multiple tasks
                if ii == 0:
                    hour = str(i)
                else:
                    hour = ''

                if task.end is None:
                    formatted_time = '{}'.format(task.start_time)
                else:
                    end_time = '{}'.format(task.end.strftime('%H:%M'))
                    formatted_time = '{}-{}'.format(task.start_time, end_time)

                # Draw hour, highlight current hour
                current_hour = time.localtime().tm_hour
                if hour != '':
                    if int(hour) == current_hour:
                        stdscr.addstr(current_line, 0, hour,
                                      curses.color_pair(5))
                    else:
                        stdscr.addstr(current_line, 0, hour,
                                      curses.color_pair(2))

                # Fill line to screen length
                stdscr.addstr(current_line, 5, ' ' * (max_x - 5), color)

                # Draw task details
                stdscr.addstr(current_line, 3, task.glyph,
                              curses.color_pair(9))
                if task.task_id != 0:
                    stdscr.addstr(current_line, 5, str(task.task_id), color)

                stdscr.addstr(current_line, offsets[2], formatted_time, color)

                if not hide_projects:
                    if task.project is None:
                        project = ''
                    else:
                        project = task.project

                    stdscr.addstr(current_line, offsets[3], project, color)
                    stdscr.addstr(current_line, offsets[4], task.description,
                                  color)
                else:
                    stdscr.addstr(current_line, offsets[3], task.description,
                                  color)

                current_line += 1
                alternate = not alternate

        stdscr.refresh()
        time.sleep(refresh_rate)


def main(argv):
    """Display a schedule report for taskwarrior."""
    parser = argparse.ArgumentParser(
        description="""Display a schedule report for taskwarrior."""
    )
    parser.add_argument(
        '-r', '--refresh', help="refresh every n seconds", type=int, default=1
    )
    parser.add_argument(
        '-s', '--scheduled', help="scheduled date: ex. 'today', 'tomorrow'",
        type=str, default='today'
    )
    parser.add_argument(
        '-a', '--all', help="show all hours, even if empty",
        action='store_true', default=False
    )
    parser.add_argument(
        '-c', '--completed', help="hide completed tasks",
        action='store_false', default=True
    )
    parser.add_argument(
        '-p', '--project', help="hide project column",
        action='store_true', default=False
    )
    args = parser.parse_args(argv)

    hide_empty = not args.all
    curses.wrapper(draw, args.refresh, hide_empty, args.scheduled,
                   args.completed, args.project)
