from celery.task.schedules import crontab
from celery import shared_task 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import requests
from project.settings import SECURITY_TOKEN
from xmljson import BadgerFish
from xml.etree.ElementTree import fromstring
import json
import re
from datetime import date, timedelta


domains = (
    "10YCS-SERBIATSOV", 
    "10YHU-MAVIR----U",
    "10YHR-HEP------M",
    "10YRO-TEL------P",
    "10YCA-BULGARIA-R"
)

dates = {
    'yesterday': (date.today() - timedelta(1)).strftime("%Y%m%d"),
    'today': date.today().strftime("%Y%m%d"),
    'tomorrow': (date.today() + timedelta(1)).strftime("%Y%m%d")
}

def urlStringFormat(forDate, domain):
    """
    Format the url for transparency.entsoe API based on date string ('today' or 'tomorrow') 
    and domain from domains tuple
    """
    if forDate == 'tomorrow':
        periodStart = dates['today']
        periodEnd = dates['tomorrow']
    if forDate == 'today':
        periodStart = dates['yesterday']
        periodEnd = dates['today']
    url = f"https://transparency.entsoe.eu/api?securityToken={SECURITY_TOKEN}&" \
        f"documentType=A44&" \
        f"in_Domain={domain}&" \
        f"out_Domain={domain}&" \
        f"periodStart={periodStart}2200&" \
        f"periodEnd={periodEnd}2200"
    return url

def xmlToJson(data):
    """
    The Badgerfish notation is used to convert xml into dictionary or json
    This notation uses "$" for xml text content and @ to prefix xml attributes
    """
    dataText = data.text
    # deleting namespace from xml because of long string repetition
    dataWithoutNameSpace = re.sub(' xmlns="[^"]+"', '', dataText, count=1)
    bf = BadgerFish(dict_type=dict)
    dataDict = bf.data(fromstring(dataWithoutNameSpace))
    return dataDict

def getCurrencyExchangeRate(fromCurrency, toCurrency):
    """
    Parameters are acronyms.
    Currency acronyms can be found on the following link:
    https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
    """
    url = f"https://api.ratesapi.io/api/latest?" \
        f"base={fromCurrency}&" \
        f"symbols={toCurrency}"
    response = requests.get(url, verify=False)
    exchangeRateDict = json.loads(response.text)
    exchangeRate = exchangeRateDict['rates']['EUR']
    return exchangeRate

def dictTransform(domain):
    """
    For Romaninan and Bulgarian domains xml consists of 2 TimeSeries. 
    This function transforms dictionary by deleting second TimeSeries and appending it's price value
    to the first TimeSeries. After the appending, the first hour price is deleted,
    therefore there is only one TimeSeries with 24 values
    """
    url = urlStringFormat('tomorrow', domain)
    data = requests.get(url)
    dataDict = xmlToJson(data)
    # Check if TimeSeries is dict or not. If it isn't, then it is an array of two TimeSeries
    if type(dataDict['Publication_MarketDocument']['TimeSeries']) is dict:
        url = urlStringFormat('today', domain)
        data = requests.get(url)
        dataDict = xmlToJson(data)

    # Transform dict into new dict without first hour and with 25. hour, 
    # which is appended from the second TimeSeries 
    priceFromSecondTimeSeries = dataDict['Publication_MarketDocument']['TimeSeries'][1]['Period']['Point']['price.amount']['$']
    del dataDict['Publication_MarketDocument']['TimeSeries'][1]
    # Transform array of one dictionary into dictionary
    dataDict['Publication_MarketDocument']['TimeSeries'] = dataDict['Publication_MarketDocument']['TimeSeries'][0]
    dataDict['Publication_MarketDocument']['TimeSeries']['Period']['Point'].append({'position': {'$': 25}, 'price.amount': {'$': priceFromSecondTimeSeries}})
    del dataDict['Publication_MarketDocument']['TimeSeries']['Period']['Point'][0]
    return dataDict

@shared_task
def getDayAheadPrices(channel_name):
    results = []

    for domain in domains:
        if domain == "10YRO-TEL------P":
            dataDict = dictTransform(domain)
            exchangeRate = getCurrencyExchangeRate('RON', 'EUR')
            position = 0
            for hourlyPriceDict in dataDict['Publication_MarketDocument']['TimeSeries']['Period']['Point']:
                dataDict['Publication_MarketDocument']['TimeSeries']['Period']['Point'][position]['price.amount']['$'] *= exchangeRate
                dataDict['Publication_MarketDocument']['TimeSeries']['Period']['Point'][position]['price.amount']['$'] = round(dataDict['Publication_MarketDocument']['TimeSeries']['Period']['Point'][position]['price.amount']['$'], 2)
                position += 1
            results.append(dataDict)
        elif domain == "10YCA-BULGARIA-R":
            dataDict = dictTransform(domain)
            exchangeRate = getCurrencyExchangeRate('BGN', 'EUR')
            position = 0
            for hourlyPriceDict in dataDict['Publication_MarketDocument']['TimeSeries']['Period']['Point']:
                dataDict['Publication_MarketDocument']['TimeSeries']['Period']['Point'][position]['price.amount']['$'] *= exchangeRate
                dataDict['Publication_MarketDocument']['TimeSeries']['Period']['Point'][position]['price.amount']['$'] = round(dataDict['Publication_MarketDocument']['TimeSeries']['Period']['Point'][position]['price.amount']['$'], 2)
                position += 1
            results.append(dataDict)
        else:
            url = urlStringFormat('tomorrow', domain)
            data = requests.get(url)
            if data.status_code == 400:
                url = urlStringFormat('today', domain)
                data = requests.get(url)
            
            dataDict = xmlToJson(data)
            results.append(dataDict)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.send)(
        channel_name,
        {
            'type': 'send.results',
            'text': results
        }
    )
