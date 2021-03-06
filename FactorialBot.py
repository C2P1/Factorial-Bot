# -*- coding: utf-8 -*-

import sys
import codecs
import praw
import time
import re
import os
import wolframalpha
from functools import reduce
from operator import mul
import random

from config_factorial import *

reload(sys)
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.setdefaultencoding('utf-8')

SINGLE_FACTORIAL_UPPER_LIMIT = 100000000000  # largest single factorial it will calculate
MULTI_FACTORIAL_UPPER_LIMIT = 500000  # largest multifactorial it will calculate
EXCLAMATION_MARK_LIMIT = 25  # most number of exclamation marks allowed in a multifactorial comment
WOLFRAM_SCIENTIFIC_START = 10  # single factorials bigger than 10! are in scientific notation on wolfram's API
SQUIGGLE = " ≈ ".decode('utf-8')


line_space = '''

'''
commentFooter = '''


---
^^I ^^am ^^a ^^bot ^^|  [^^Info ^^at ^^/r/Factorial-Bot](http://www.reddit.com/r/factorialbot) ^^| ''' + \
                '''[^^Contact ](https://www.reddit.com/message/compose/?to=''' + author + '''&subject=Factorial-Bot)'''


def recent_posts():
    my_time = int(time.time())

    try:
        for sub in subreddit_post_list:
            subreddit = reddit.subreddit(sub)
            for submission in subreddit.new(limit=3):
                sub_age = int(my_time - submission.created_utc)
                print(sub_age)
                if sub_age < 1000:
                    result = extract_factorial(submission, submission.title)
                    if result is not None:
                        num = result['number']
                        is_decimal = result['is_decimal']
                        comment_to_add = construct_comment(num, is_decimal)
                        comment = submission.reply(comment_to_add)
                        reddit.redditor(author).message("Comment made!", str(comment.permalink()))

    except Exception as error:
        print(str(error))


# remove all spaces and commas from the input
def format_number(text_input):
    for char in text_input:
        if char.isalpha():
            text_input = text_input.replace(char, "", 1)
    spaceless = "".join(text_input.split(" "))
    num_periods = spaceless.count(".")
    num_commas = spaceless.count(",")

    if num_periods == 1 and num_commas == 0:
        split = spaceless.split(".")

        # check if thousand separator or decimal point
        if len(split[1][-1]) == 3:
            return "".join(split)
        else:
            return spaceless

    if num_periods == 0 and num_commas == 1:
        split = spaceless.split(",")

        # check if thousand separator or decimal point
        if len(split[1][:-1]) == 3:
            return "".join(split)
        else:
            return spaceless

    if num_periods >= 2:
        removed_periods = spaceless.replace(".", "")
        if num_commas == 1:
            removed_periods = removed_periods.replace(",", ".")
        if num_commas > 1:
            return None

        return removed_periods
    elif num_commas >= 2:
        removed_commas = spaceless.replace(",", "")
        if num_periods > 1:
            return None
        return removed_commas

    if num_periods == 1 and num_commas == 1:
        period_index = spaceless.index('.')
        comma_index = spaceless.index(',')

        # if commas comes first e.g 4,500.10
        if period_index > comma_index:
            return spaceless.replace(",", "")

        # period comes first e.g 4.500,10
        if period_index < comma_index:
            step = spaceless.replace(".", "")
            return step.replace(",", ".")

    return spaceless.replace(",", "")


def multifactorial(n, m):
    return reduce(mul, range(n, 0, -m))


def extract_factorial(submission, content):

    packet = None

    # check tp see if there is a log of posts already replied to
    if not os.path.isfile("posts_replied_to_by_factorial.txt"):
        # start an empty list to fill with the ids of posts replied to
        posts_replied_to = []

    # If a log does exist, load the list of posts already replied to
    else:
        # Read the file into a list and remove any empty values
        with open("posts_replied_to_by_factorial.txt", "r") as f:
            posts_replied_to = f.read()
            posts_replied_to = posts_replied_to.split("\n")
            posts_replied_to = filter(None, posts_replied_to)
            posts_replied_to = list(posts_replied_to)

        if submission.id not in posts_replied_to:
            # get the post title
            title = format_number(content)

            # regex matching for any number of digits before any number of exclamation marks
            if re.search(r'(\d+?.)*\d+!+', title):
                factorial = re.search(r'(\d+?.)*\d+!+', title)

                # count the parentheses in the factorial
                count = 0
                for char in str(title):
                    if char == '(':
                        count += 1
                    else:
                        break

                # find the number of exclamation marks used
                excalamtion = re.search(r'!+', factorial.group())
                number_of_exclamations = len(excalamtion.group())
                # take the integer part of the string, exclude the exclamation marks
                string_num = factorial.group()[:-number_of_exclamations]

                # count number of 'decimal points'
                number_of_points = string_num.count('.')
                is_decimal = False
                if number_of_points > 1:
                    num = int("".join(string_num.split(".")))
                elif number_of_points == 0:
                    num = int(string_num)
                else:
                    num = float(string_num)
                    is_decimal = True

                if (')!' * count) in title:
                    packet = {'number': ('(' * count) + factorial.group() + (')!' * count), 'is_decimal': is_decimal}
                elif number_of_exclamations == 1:
                    if num < SINGLE_FACTORIAL_UPPER_LIMIT:
                        packet = {'number': factorial.group(), 'is_decimal': is_decimal}
                else:
                    if num < MULTI_FACTORIAL_UPPER_LIMIT:
                        if number_of_exclamations < EXCLAMATION_MARK_LIMIT:

                            ans = multifactorial(num, number_of_exclamations)

                            string_ans = str(ans)
                            if len(string_ans) > 8:
                                abc = string_ans[0:3]
                                prefix = round(int(abc) / 100.0, 2)
                                power = len(string_ans) - 1
                                ans = str(prefix) + ' x 10^' + str(power)
                                sign = SQUIGGLE
                            else:
                                sign = " = "

                            # construct the comment to be posted
                            comment = str(num) + "!" * number_of_exclamations + sign + str(ans) + \
                                ' ' + commentFooter

                            com = submission.reply(comment)
                            reddit.redditor(author).message("Comment made!", str(com.permalink()))

                # Store the current id into list
                posts_replied_to.append(submission.id)

    # Write our updated list back to the file
    with open("posts_replied_to_by_factorial.txt", "w") as f:
        for post_id in posts_replied_to:
            f.write('{0}\n'.format(post_id))

    return packet


def relative_size_fact(power):
    try:
        power = int(power)
    except ValueError:
        return " "

    if power == 4:
        return diameter_earth
    elif power == 5 or power == 6:
        return area_texas
    if power == 7:
        return seconds_decade
    if power == 8:
        return seconds_decade
    if power == 9:
        return diameter_neptune_orbit
    if power == 10:
        rdn = random.randint(1, 2)
        if rdn == 1:
            return seconds_millennium
        else:
            return years_age_universe
    if power == 12:
        return years_age_universe

    if power == 18:
        return seconds_age_universe
    if power == 19:
        return diameter_milky_way
    if power == 20:
        return seconds_age_universe
    if power == 23:
        return diameter_universe

    if 49 <= power <= 52:
        return diameter_op_mom
    if 51 <= power <= 53:
        return card_combos
    if 75 <= power <= 100:
        return atoms_universe


def number_fact(number):
    if number == 24:
        return "24 is the smallest number with 3 representations as a sum of 2 distinct primes:     " + \
          "24 = 5 + 19 = 7 + 17 = 11 + 13"
    if number == 120:
        return "120 = binomial(15 + 1, 2) is the 15th triangular number."
    if number == 720:
        return "720 has a representation as a sum of 2 squares:     " + \
               "720 = 12^2 + 24^2"
    if number == 3628800:
        return "3628800 is a number that cannot be written as a sum of 3 squares."


def comment_control():
    for comment in reddit.inbox.mentions(limit=2):
        try:
            result = comment_parse(comment)
            if result is not None:
                num = result['number']
                is_decimal = result['is_decimal']
                comment_to_make = construct_comment(num, is_decimal)
                com = comment.reply(comment_to_make)
                reddit.redditor(author).message("Comment made!", str(com.permalink()))
        except TypeError as e:
            reddit.redditor(author).message(str(e), comment.body + line_space + comment.permalink())
            print(e)

    for comment in reddit.inbox.comment_replies(limit=2):
        try:
            result = comment_parse(comment)
            if result is not None:
                num = result['number']
                is_decimal = result['is_decimal']
                comment_to_make = construct_comment(num, is_decimal)
                com = comment.reply(comment_to_make)
                reddit.redditor(author).message("Comment made!", str(com.permalink()))
        except TypeError as e:
            reddit.redditor(author).message(str(e), comment.body + line_space + comment.permalink())
            print(e)


def comment_parse(comment):
    text = comment.body
    if "+/u/factorial-bot" in text.lower() or "+u/factorial-bot" in text.lower():
        if re.search(r'(\d+?.)*\d+!+', text):
            return extract_factorial(comment, text)
        else:
            parent = comment.parent()
            if parent.author != "Factorial-Bot":
                return extract_factorial(parent, parent.body)


def construct_comment(num, is_decimal):
    print('constructing comment...')
    # login in to wolfram alpha and submit the factorial to be calculated
    app_id = wolfram_app_id
    client = wolframalpha.Client(app_id)
    res = client.query(str(num))

    primaries = []
    for p in res.results:
        primaries = [p.text]

    # put the result(s) in to a list
    lines = []

    for pod in res.pods:
        for sub in pod.subpods:
            lines.append(sub['plaintext'])

    for p in res:
        if p.title == 'Power of 10 representation':
            for sub in p.subpod:
                primaries.append(sub['plaintext'])

    # the factorial that was queried
    orig = num

    lines = [x for x in lines if x is not None]

    if is_decimal:
        if "..." in lines[1]:
            lines[1] = lines[1].replace("...", "")
        comment_to_add = str(num) + " = " + lines[1] + ' ' + commentFooter
        return comment_to_add

    if "..." in primaries[0]:
        primaries[0] = primaries[0].replace("...", "")

    # if the number to calculate the factorial of is bigger than 10 then the answer is returned in scientific form
    # and thus needs more processing to format it correctly in to a comment
    if num > WOLFRAM_SCIENTIFIC_START:
        ans = primaries[0]

        if ' × ' in str(ans):

            # round the mantissa of the answer to two decimal places
            mantissa = str(round(float(primaries[0][:8]), 2))

            # find the exponent in the string
            space = ans.find(' ')
            exponent = ans[space + 3:]

            # format the factorial in scientific x10 notation
            factorial = str(mantissa) + ' x ' + exponent

            # format the factorial in scientific e notation
            # e_factorial = str(round(float(primaries[0][:8]), 4)) + 'e+' + exponent[3:]

            if relative_size_fact(exponent[3:]) is not None:
                # construct the entire comment to be posted
                comment_to_add = str(orig) + SQUIGGLE + factorial + '  ' + line_space + '---  ' + line_space + \
                                 relative_size_fact(exponent[3:]) + '  ' + line_space + commentFooter
            else:
                # construct the entire comment to be posted
                comment_to_add = str(orig) + SQUIGGLE + factorial + '  ' + line_space + commentFooter

        else:

            comment_to_add = str(orig) + " = " + primaries[0] + '  ' + line_space + commentFooter

    else:
        # construct the comment to be posted
        comment_to_add = str(orig) + " = " + lines[1] + ' ' + commentFooter

    print(comment_to_add)

    return comment_to_add

if __name__ == "__main__":

    reddit = praw.Reddit(client_id=client_id,
                         client_secret=client_secret,
                         password=password,
                         user_agent='fact calc',
                         username=username)

    now = time.localtime(time.time())
    year, month, day, hour, minute, second, weekday, yearday, daylight = now

    times = "%02d:%02d" % (hour, minute)

    recent_posts()
    comment_control()

    if "11:03" > times > "11:00":
        reddit.redditor(author).message('Running', times)
    elif "23:03" > times > "23:00":
        reddit.redditor(author).message('Running', times)
