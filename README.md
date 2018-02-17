# Factorial-Bot
Originally built as the in house bot for the subreddit [/r/unexpectedfactorial](https://www.reddit.com/r/unexpectedfactorial/) in which it would calculate the value of any factorials in the post title, the bot's functionality was expanded to be able to be called by users to calculate a factorial anywhere on reddit. Initially designed to continuously run on a raspberry pi. 

## Usage

##### There are two ways in which /u/Factorial-Bot can be used in the comments:

1. By posting a factorial followed by +/u/Factorial-Bot e.g

    > 33! +/u/factorial-bot

2. If you come across a comment containing a factorial then you can reply to the comment that contains a factorial with your own comment which should contain the text 

    > +/u/factorial-bot  

    The bot will then calculate the factorial in the parent comment and reply to your comment. 

##### /u/Factorial-Bot will also reply to factorials in post titles (as seen on [/r/unexpectedfactorial](https://www.reddit.com/r/unexpectedfactorial/)). It only does this on specific subreddits that have opted in.

## Running The Script
###### Requires the following variables to be in a factorial_config.py file:
```
username 
password 
author 
wolfram_app_id
subreddit_post_list 
client_id
client_secret
```

