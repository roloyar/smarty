from slackbot.bot import Bot, respond_to, listen_to
import re
import json
import time
import random
from settings import COMPANY_NAME, EXAMPLE_URL, EXAMPLE_URL_TITLE, DOMAIN_NAMES
from analytics import get_report

import sys

def extract_dates(request):
	def getDates(r):
		keys = r.split(" ")
		if keys[-2] == 'from':
			date_from = date_to = keys[-1]
		else:
			date_to = keys[-1]
			date_from = keys[-3]
		return [date_from,date_to]		

	if ' from ' in request:
		from_to_dates = getDates(request)
	else:
		words = request.split(" ")
		date = words[-1]
		from_to_dates = [date, date]
		
	return from_to_dates

def AnalyticsParams(word, request):
	'''If words "top" or "url" in request'''

	from_to_dates = extract_dates(request)

	p = re.compile('(%s)(\s)(\S*)' % word)
	result = re.search(p,request)

	if word == 'top':
		top_number = int(result.group(3))
		page_path = ''
	else: # that is if word is "url"
		top_number = 1
		page_path = result.group(3)
		# get rid of the domain name
		for name in DOMAIN_NAMES:
			page_path = page_path.replace(name,'')
		page_path = page_path.replace('<','').replace('>','')

	analytics_request_params = {
		'word': word,
		'top_number': top_number,
		'from_to_dates': from_to_dates,
		'path': page_path
	}

	return analytics_request_params

def main():
	bot = Bot()
	bot.run()

@respond_to("^hi|^hello|^hi there|^what's up", re.IGNORECASE)
def hi(message):
	responses = ['Hello','Hello there','Hi there','Sup','Hey']
	message.reply(random.choice(responses))


@respond_to('^help', re.IGNORECASE)
def help(message):
	reply = 'To get info on what bounce rate is, just ask me "what is bounce rate?"\n\
*`Using reports:`*\n\
Start your request with the *report* keyword.\n\
The *report* syntax: \n\
>The *top* keyword: \n\
```report top 7 from 2016-02-01 to today```\n\
In this example above, `report`, `top`, `from` and `to` are all keywords. They need to be in this particular order.\n\
This query will give you a list of top 7 pages from Feb 1 2016 until today.\n\
  \n\
*The `today` term simply means "up to now"\n\
*The date is in YEAR-MONTH-DATE format with dashes.\n\
*Number after `top` *needs to be below or equal to 20*.\n\
*All results are *arranged by the number of page views* (unique and non unique)\n\
  \n\
Again, the structure is `report` _space_ `top` _space_ *number* _space_ `from` \
_date_ (can also be today or yesterday) _space_ `to` _space_ _date_.\n\
You can also say things like \n\
```report top 10 yesterday```\n\
or\n\
```report top 20 today```\n\
or\n\
```report top 5 from 2015-11-10 to 2016-01-01```\n\
>The *url* keyword: \n\
Now, if you want to get something else then a list of top pages, \
you can also say `report url` followed by the full URL of the page on '+COMPANY_NAME+' you need analyzed, plus the date or dates.\n\
So, *for example:*\n\
```report url '+EXAMPLE_URL+' from 2014-11-28 to today```\n\
Will tell you all stats for the *'+EXAMPLE_URL_TITLE+'* page on '+COMPANY_NAME+' for the respective time period.'

	message.reply(reply)

@respond_to('report(.*)', re.IGNORECASE)
def report_with_details(message, request):

	if request == '':
		message.reply('Please specify a date or a time frame. Type "help" for details.')
	else:
		message.reply('Just a sec, working...')
		try:
			if ' top ' in request:
				params = AnalyticsParams('top',request)
			else: # that is if url in request
				params = AnalyticsParams('url',request)

			analytics_report = get_report(**params)

			attachments = []
			raiting = 0
			for item in analytics_report:
				raiting += 1

				attachment = {
					"fallback": item['title'].decode('utf-8') + ', pageviews: ' + item['pageviews'],
					"title": item['title'].decode('utf-8'),
					"title_link": item['url'],
					"fields": [
						# {
						# "title": "Rating: ",
						# "value": str(raiting),
						# "short": "true"
						# },
						{
						"title": "Page views",
						"value": item['pageviews'],
						"short": "true"
						},
						{
						"title": "Avg. time on page",
						"value": item['avg_time'],
						"short": "true"
						},
						{
						"title": "Bounce rate",
						"value": item['bounce_rate'],
						"short": "true"
						},
						{
						"title": "Facebook stats (ALL TIME)",
						"value": "Shares: " + item['fb_shares'],
						"short": "true"
						}]
					# 'color': '#36A64F'
				}

				# if only stats for one URL requested, also get the top sources data
				if ' url ' in request:
					sources_text = ''
					for source in item['sources']:
						sources_text += str(source['source_name']) + ', '

					attachment["fields"].append({
						"title": "Top 5 sources (the smaller request time frame, the more accurate this list is):",
						"value": sources_text,
						"short": "true"
						})
					attachment['color'] = "#2FA44F"

				attachments.append(attachment)

			if ' top ' in request:
				message.reply('Okay, here are the *top '+str(params['top_number'])+' pages*, time span is: '+params['from_to_dates'][0]+' - '+params['from_to_dates'][1])
			else:
				message.reply('Okay, here are the stats for the *single page* you requested, time span is: '+params['from_to_dates'][0]+' - '+params['from_to_dates'][1])
			message.send_webapi('', json.dumps(attachments))

		except:
			message.reply('Oops. Looks like something went wrong. Are you sure you formated your query correctly? Type "help" for instructions.')
			# Also log error text
			# e = sys.exc_info()[0]
			# message.reply(e)



# @respond_to('reported', re.IGNORECASE)
# def report(message):

# 	message.reply('Just a sec, working')

# 	analytics_report = get_report_yesterday()

# 	attachments = []
# 	raiting = 0
# 	for item in analytics_report:
# 		raiting += 1
# 		attachment = {
# 			'fallback': str(raiting),	
# 			'text': 'Page: ' + item['title'].decode('utf-8'),
# 			"fields": [
# 				{
# 				"title": "Rating: ",
# 				"value": str(raiting),
# 				"short": "true"
# 				},
# 				{
# 				"title": "Page views",
# 				"value": item['pageviews'],
# 				"short": "true"
# 				},
# 				{
# 				"title": "Avg. time on page",
# 				"value": item['avg_time'],
# 				"short": "true"
# 				},
# 				{
# 				"title": "Bounce rate",
# 				"value": item['bounce_rate'],
# 				"short": "true"
# 				}],
# 			# 'color': '#36A64F'
# 		}
# 		attachments.append(attachment)

# 	message.reply('Okay, here are the *top 10 stories from yesterday*')
# 	message.send_webapi('', json.dumps(attachments))

@respond_to('bounce rate', re.IGNORECASE)
def bounce_rate(message):

	text = '>Bounce rate is the percentage of single page visits (or web sessions).\n\
It is the number of visits in which a person leaves your website from the landing page without browsing any further.\n\
In simpler terms, an 82 percent bounce rate would mean that only 18 percent of all visitors \
also visited other pages of the ' + COMPANY_NAME
	message.reply(text)

@respond_to('I love you', re.IGNORECASE)
def love(message):

	attachments = [{
		'fallback': "I love you too!",
		'title': "I love you too!!! :smiley: :sunflower: :rose:",
		"image_url": "http://vignette2.wikia.nocookie.net/shipping/images/6/66/Pixel_heart_icon.png/revision/latest?cb=20151011174450",
		'color': '#D50200'
	}]
	message.send_webapi('', json.dumps(attachments))

if __name__ == "__main__":
	main()