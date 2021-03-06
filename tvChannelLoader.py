#!/usr/bin/env python

import urllib2
from bs4 import BeautifulSoup
from parsingLibrary import loadHtmlTags, parseChannel, remove_duplicate_elements
from pymongo import MongoClient
from mongoConfiguration import load_mongo_configuration

mongo_address, mongo_port = load_mongo_configuration()
client = MongoClient(mongo_address, mongo_port)

db = client['freeview']
channelCollection = db['tvChannel']
channelCollection.drop()
channelCategoryCollection = db['tvChannelCategory']
channelCategoryCollection.drop()
channelProviderCollection = db['tvChannelProvider']
channelProviderCollection.drop()


def get_channels(url):
    url_channels = 'http://tvguideuk.telegraph.co.uk/' + url
    print url
    a = BeautifulSoup(urllib2.urlopen(url_channels).read())
    channels = a.findAll("div", {"class": "channel_name"})
    list_channels = []
    for channel in channels:
        list_channels.append(channel.text)
    return list_channels


def add_type_to_channel(channels_classified, channels_by_type, key, value):
    for channel in channels_by_type:
        if channel not in channels_classified:
            channels_classified[channel] = {}
            channels_classified[channel][key] = []
            channels_classified[channel][key].append(value.upper())
            channels_classified[channel]['name'] = parseChannel(channel.upper())
        else:
            if key in channels_classified[channel]:
                channels_classified[channel][key].append(value.upper())
            else:
                channels_classified[channel][key] = []
                channels_classified[channel][key].append(value.upper())
    return channels_classified


def find_channel_classifed(tags):
    for tag_url in tags:
        # if 'All' in tag_url:
        #     all_channels = getChannels(tag_url)
        if 'Freeview' in tag_url:
            freeview_channels = get_channels(tag_url)
        if 'Terrestrial' in tag_url:
            terrestrial_channels = get_channels(tag_url)
        if 'Sky & Cable' in tag_url:
            cable_all_channels = get_channels(tag_url)
        if 'Films' in tag_url:
            films_channels = get_channels(tag_url)
        if 'Sport' in tag_url:
            sport_channels = get_channels(tag_url)
        if 'News & Doc' in tag_url:
            news_channels = get_channels(tag_url)
        if 'Kids' in tag_url:
            kids_channels = get_channels(tag_url)
        if 'Radio' in tag_url:
            radio_channels = get_channels(tag_url)

    channels_classified = {}
    add_type_to_channel(channels_classified, freeview_channels, "provider", "FREEVIEW")
    add_type_to_channel(channels_classified, terrestrial_channels, "provider", "TERRESTRIAL")
    add_type_to_channel(channels_classified, cable_all_channels, "provider", "SKY & CABLE")

    add_type_to_channel(channels_classified, films_channels, "category", "FILMS")
    add_type_to_channel(channels_classified, sport_channels, "category", "SPORTS")
    add_type_to_channel(channels_classified, news_channels, "category", "NEWS & DOCUMENTARY")
    add_type_to_channel(channels_classified, kids_channels, "category", "KIDS")
    add_type_to_channel(channels_classified, radio_channels, "category", "RADIO")

    return channels_classified

from datetime import datetime

day = datetime.now().day
month = datetime.now().month
year = datetime.now().year

hours = ['12am', '2am', '4am', '6am', '8am', '10am', '12pm', '2pm', '4pm', '6pm', '8pm', '10pm']
channels_classified = {}
for hour in hours:
    tags = loadHtmlTags(year, month, day, hour, 'All')
    channels_classified_temp = find_channel_classifed(tags)
    print '-------- ' + hour
    for channel_classified_temp in channels_classified_temp:
        if channel_classified_temp in channels_classified:
            if channels_classified_temp[channel_classified_temp] != channels_classified[channel_classified_temp]:
                print "--------  DIFFERENT"
                print channels_classified_temp[channel_classified_temp]
                print channels_classified[channel_classified_temp]
        else:
            channels_classified[channel_classified_temp] = channels_classified_temp[channel_classified_temp]
            print channel_classified_temp + ' INSERTED'

for channel in channels_classified:
    if 'category' not in channels_classified[channel]:
        channels_classified[channel]['category'] = ['GENERIC']
    if 'provider' in channels_classified[channel]:
        channels_classified[channel]['provider']= remove_duplicate_elements(channels_classified[channel]['provider'])
    else:
        channels_classified[channel]['provider'] = ['UNKNOWN']
    channelCollection.insert(channels_classified[channel])

providers = ["FREEVIEW", "TERRESTRIAL", "SKY & CABLE", "UNKOWN"]
categories = ["FILMS", "SPORTS", "NEWS & DOCUMENTARY", "KIDS", "RADIO", "GENERIC"]

for provider in providers:
    json_to_insert = {}
    json_to_insert['provider'] = provider
    channelProviderCollection.insert(json_to_insert)

for category in categories:
    json_to_insert = {}
    json_to_insert['category'] = category
    channelCategoryCollection.insert(json_to_insert)
