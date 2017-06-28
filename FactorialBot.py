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

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

SINGLE_FACTORIAL_UPPER_LIMIT = 1000000000  # largest single factorial it will calculate
MULTI_FACTORIAL_UPPER_LIMIT = 10000  # largest multifactorial it will calculate
EXCLAMATION_MARK_LIMIT = 6  # most number of exclamation marks allowed in a multifactorial comment
WOLFRAM_SCIENTIFIC_START = 10  # single factorials bigger than 10! are in scientific notation on wolfram's API
WOLFRAM_FULL_ANSWER_CUT = 11077  # factorials bigger than 11077! are no longer written out in full in the API
SQUIGGLE = " ≈ ".decode('utf-8')

line_space = '''

'''
commentFooter = '''

---  
^^I ^^am ^^a ^^bot, ^^this ^^was ^^performed ^^automatically. ^^Please ^^message ^^/u/''' + author + \
                ''' ^^if ^^you ^^have ^^any ^^questions.'''


def recent_posts():
    my_time = int(time.time())

    try:
        for sub in subreddit_post_list:
            subreddit = r.get_subreddit(sub)
            for submission in subreddit.get_new(limit=3):
                sub_age = int(my_time - submission.created_utc)
                print(sub_age)
                if sub_age < 1000:
                    title_parse(submission)
                # comment_parse(submission)

    except Exception as error:
        print(str(error))
        return 1


# remove all spaces and commas from the input
def string_split(text_input):
    string_one = "".join(text_input.split(" "))
    string_two = "".join(string_one.split(","))
    return string_two


def multifactorial(n, m):
    return reduce(mul, range(n, 0, -m))


def title_parse(submission):
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
            title = string_split(submission.title)
            # regex matching for any number of digits before any number of exclamation marks
            if re.search(r'(\d+?.)*\d+!+', title):
                factorial = re.search(r'(\d+?.)*\d+!+', title)
                # find the number of exclamation marks used
                excalamtion = re.search(r'!+', factorial.group())
                number_of_exclamations = len(excalamtion.group())
                # take the integer part of the string, exclude the exclamation marks
                string_num = factorial.group()[:-number_of_exclamations]

                # count number of 'decimal points'
                number_of_points = string_num.count('.')
                print(number_of_points)
                is_decimal = False
                if number_of_points > 1:
                    num = int("".join(string_num.split(".")))
                elif number_of_points == 0:
                    num = int(string_num)
                else:
                    num = float(string_num)
                    is_decimal = True

                if number_of_exclamations == 1:
                    if num < SINGLE_FACTORIAL_UPPER_LIMIT:
                        reply_to_post(num, submission, is_decimal)
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

                            submission.add_comment(comment)

                # Store the current id into list
                posts_replied_to.append(submission.id)

    # Write our updated list back to the file
    with open("posts_replied_to_by_factorial.txt", "w") as f:
        for post_id in posts_replied_to:
            f.write('{0}\n'.format(post_id))


def reply_to_post(num, submission, is_decimal):
    print('replying to post...')
    # login in to wolfram alpha and submit the factorial to be calculated
    app_id = wolfram_app_id
    client = wolframalpha.Client(app_id)
    res = client.query(str(num) + '!')

    # put the result(s) in to a list
    lines = []
    for pod in res.pods:
        for sub in pod.subpods:
            lines.append(sub['plaintext'])

    # the factorial that was queried
    orig = lines[0]

    lines = [x for x in lines if x is not None]

    for item in lines:
        if "decimal digits" in item:
            digits = item

    if is_decimal:
        comment = str(orig) + " = " + lines[1] + ' ' + commentFooter
        print(comment)
        submission.add_comment(comment)
        return

    # if the number to calculate the factorial of is bigger than 10 then the answer is returned in scientific form
    # and thus needs more processing to format it correctly in to a comment
    if num > WOLFRAM_SCIENTIFIC_START:
        # once the number to calculate the factorial of passes a certain point, the full answer of every single digit
        # is no longer written out and so the first result is to be taken instead of the second
        if num > WOLFRAM_FULL_ANSWER_CUT:
            ans = lines[1]
        else:
            ans = lines[2]
        print(ans)
        # round the mantissa of the answer to two decimal places
        mantissa = str(round(float(ans[:8]), 2))

        # find the exponent in the string
        space = ans.find(' ')
        exponent = ans[space + 3:]

        # format the factorial in scientific x10 notation
        factorial = str(mantissa) + ' x ' + exponent

        # format the factorial in scientific e notation
        # e_factorial = str(round(float(ans[:8]), 4)) + 'e+' + exponent[3:]

        number_length = "Number length: " + digits

        print("here")
        print(exponent[3:])
        print(relative_size_fact(exponent[3:]))
        print(1)

        # construct the entire comment to be posted
        comment = str(orig) + SQUIGGLE + factorial + '  ' + line_space + '---  ' + line_space + \
            number_length + '  ' + line_space + '---  ' + line_space + relative_size_fact(exponent[3:]) + '  ' + \
            line_space + commentFooter

    else:
        # construct the comment to be posted
        comment = str(orig) + " = " + lines[1] + ' ' + commentFooter

    print(comment)

    submission.add_comment(comment)


def relative_size_fact(power):
    try:
        power = int(power)
    except Exception as e:
        return " "
    diameter_earth = "The average diameter of planet Earth is 1.27 x 10^4 km"
    area_texas = "The area of texas is 2.686 x 10^5 square miles"

    seconds_decade = "There are 3.156 x 10^8 seconds in a decade."
    diameter_neptune_orbit = "The diameter of Neptune's orbit is 8.99683742 x 10^9 km"
    seconds_millennium = "There are 3.156 x 10^10 seconds in a millennium"
    years_age_universe = "The age of the universe is 1.4 x 10^10 years."
    seconds_age_universe = "The age of the universe is 4.3 x 10^17 seconds."
    diameter_milky_way = "The average diameter of the Milky Way is 9.5 x 10^17 km"
    diameter_universe = "The diameter of the observable universe is 8.8 x 10^23 km"

    diameter_op_mom = "The diameter of OP's mom is 7.638 x 10^50 m"
    card_combos = "There are 52! = 8.07 x 10^67 possible combinations of a pack of 52 cards."
    atoms_universe = "There are 1 x 10^80 atoms in the universe"

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


# def comment_parse(submission):
#
#     # Have we run this code before? If not, create an empty list
#     if not os.path.isfile("factorial_comments.txt"):
#         posts_replied_to = []
#
#     # If we have run the code before, load the list of posts we have replied to
#     else:
#         # Read the file into a list and remove any empty values
#         with open("factorial_comments.txt", "r") as f:
#             posts_replied_to = f.read()
#             posts_replied_to = posts_replied_to.split("\n")
#             posts_replied_to = filter(None, posts_replied_to)
#             posts_replied_to = list(posts_replied_to)
#
#     try:
#         for sub in subreddit_comment_list:
#             # Get the top 15 values from the subreddit
#             subreddit = r.get_subreddit(sub)
#             comments = subreddit.get_comments(limit=30)
#             # print(1)
#             for comment in comments:
#                 # If we haven't replied to this post before
#                 # print(2)
#                 if comment.id not in posts_replied_to:
#                     author = comment.author.name
#
#                     parent_name = parent.author.name
#                     if author != r.user.me():
#                         try:
#                             parent = r.get_info(thing_id=comment.parent_id)
#                             parent_name != r.user.me():
#
#     content = comment.body


if __name__ == "__main__":

    try:
        r = praw.Reddit(user_agent="FactorialCalc")
        r.login(username, password)
    except Exception as e:
        print("Login Error")

    now = time.localtime(time.time())
    year, month, day, hour, minute, second, weekday, yearday, daylight = now

    times = "%02d:%02d" % (hour, minute)

    recent_posts()
    # comment_parse()

    if "11:03" > times > "11:00":
        r.send_message(author, 'Running Fine', 'A-OK at ' + times)
    elif "23:03" > times > "23:00":
        r.send_message(author, 'Running Fine', 'A-OK at ' + times)
