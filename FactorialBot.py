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
from config_factorial import *

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

SINGLE_FACTORIAL_UPPER_LIMIT = 1000000000  # largest single factorial it will calculate
MULTI_FACTORIAL_UPPER_LIMIT = 10000  # largest multifactorial it will calculate
EXCLAMATION_MARK_LIMIT = 6  # most number of exclamation marks allowed in a multifactorial comment
WOLFRAM_SCIENTIFIC_START = 10  # single factorials bigger than 10! are in scientific notation on wolfram's API
WOLFRAM_FULL_ANSWER_CUT = 11077  # factorials bigger than 11077! are no longer written out in full in the API

line_space = '''

'''
commentFooter = '''

---  
^^I ^^am ^^a ^^bot ^^testing, ^^this ^^was ^^performed ^^automatically. ^^Please ^^message ^^/u/''' + author +\
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
            if re.search(r'\d+\!+', title):
                factorial = re.search(r'\d+\!+', title)
                # find the number of exclamation marks used
                excalamtion = re.search(r'\!+', factorial.group())
                number_of_exclamations = len(excalamtion.group())
                # take the integer part of the string, exclude the exclamation marks
                num = int(factorial.group()[:-number_of_exclamations])

                if number_of_exclamations == 1:
                    print(num)
                    if num < SINGLE_FACTORIAL_UPPER_LIMIT:
                        reply_to_post(num, submission)
                else:
                    if num < MULTI_FACTORIAL_UPPER_LIMIT:
                        if number_of_exclamations < EXCLAMATION_MARK_LIMIT:
                            ans = multifactorial(num, number_of_exclamations)
                            ansstr = str(ans)
                            # if len(ansstr) > 8:
                            #    abc = ansstr[0:4]
                            #    prefix = round(int(abc) / 1000.0, 2)
                            #    power = len(ansstr) - 3
                            #    factorial = str(prefix) + ' x 10^' + str(power)
                            #
                            #    squiggle = " ≈ ".decode('utf-8')
                            #    comment = str(num) + "!" + squiggle + factorial + ' ' + commentFooter
                            # else:

                            # construct the comment to be posted
                            comment = str(num) + "!" * number_of_exclamations + " = " + str(ans) + ' ' + commentFooter

                            submission.add_comment(comment)

                # Store the current id into list
                posts_replied_to.append(submission.id)

    # Write our updated list back to the file
    with open("posts_replied_to_by_factorial.txt", "w") as f:
        for post_id in posts_replied_to:
            f.write('{0}\n'.format(post_id))


def reply_to_post(num, submission):
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
        e_factorial = str(round(float(ans[:8]), 4)) + 'e+' + exponent[3:]

        # approximation sign
        squiggle = " ≈ ".decode('utf-8')

        # construct the entire comment to be posted
        comment = str(orig) + squiggle + factorial + ' ' + \
                  line_space + str(orig) + squiggle + e_factorial + commentFooter

    else:
        # construct the comment to be posted
        comment = str(orig) + " = " + lines[1] + ' ' + commentFooter

    print(comment)

    submission.add_comment(comment)


if __name__ == "__main__":

    try:
        r = praw.Reddit(user_agent="FactorialBot")
        r.login(username, password)
    except Exception as e:
        print("Login Error")

    now = time.localtime(time.time())
    year, month, day, hour, minute, second, weekday, yearday, daylight = now

    times = "%02d:%02d" % (hour, minute)

    recent_posts()

    if "11:03" > times > "11:00":
        r.send_message(author, 'Running Fine', 'A-OK at ' + times)
    elif "23:03" > times > "23:00":
        r.send_message(author, 'Running Fine', 'A-OK at ' + times)
