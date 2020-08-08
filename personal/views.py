import time
import json
from copy import deepcopy as copy

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.db.models import Max

from .models import Profile, ImageFile, MatchDetail, MatchHistory, APICallHistory, APIKey, KrogerServiceData
from .forms import UploadFileForm, CreateNewProfileForm, ImageSearchForm
from .filesystem import handle_image_upload, handle_create_new_user

from riotwatcher import LolWatcher, ApiError
import pandas as pd
from asteval import Interpreter
import requests

#globals
try:
    riot_api_key = APIKey.objects.filter(service__exact='Riot').order_by('-time')[:1][0].key #this should come from db in production
    watcher = LolWatcher(riot_api_key)
    kroger_api_credentials = APIKey.objects.filter(service__exact='Kroger').order_by('-time')[:1][0].key
except:
    pass

# class declarations


# non-page returning helper methods
#api call manager so we don't exceed the call limit
def APICall(call='matchlist_by_account', args={'summoner':'Small_Crawler', 'region':'na1'}):
    try:
        history = APICallHistory.objects.filter(service__exact='Riot').order_by('-time')
        calls_ago_100 = history[99].time
        calls_ago_20 = history[19].time
    except: # if there happens to be no object
        calls_ago_100 = 0
        calls_ago_20 = 0

    one_second_ago = int(time.time()*1000) - 1000
    two_minutes_ago = int(time.time()*1000) - 120000
    # rate limit is 100 calls in 2 minutes, or 20 calls per second
    if calls_ago_100 > two_minutes_ago or calls_ago_20 > one_second_ago:
        print('sleeping on it')
        time.sleep(1)
        return APICall(call=call, args=args)
    else:
        to_store = APICallHistory(time=int(time.time()*1000),desc='a responsible api call')
        to_store.save()
        try:
            if call == 'match_detail':
                return watcher.match.by_id(args['region'],args['gameId'])
            if call == 'matchlist_by_account':
                return watcher.match.matchlist_by_account(args['region'], args['accountId'],begin_time=args['begin_time'])
            if call == 'summoner_by_name':
                return watcher.summoner.by_name(args['region'], args['summoner'])
        except Exception as e:
            print(e, 'error in APICall')
            return {'matches':[]}

def updateMatchHistory(summoner='Small_Crawler', region='na1', return_latest=True, to_return=1):
     #this is wrong, but won't be an issue unless there is more than one summoner in the db
    try:
        latest_detail = MatchHistory.objects.all().latest('time')
        begin = latest_detail.time + 1
    except Exception as e: # if there happens to be no object
        print(e, 'could not get latest detail time')
        begin = 0

    me = APICall(call='summoner_by_name',args={'summoner':summoner,'region':region})
    print(me)
    my_matches = APICall(call='matchlist_by_account',args={'region':region,'accountId':me['accountId'],'begin_time':begin,'end_time':int(time.time()*1000)})
    
    my_matches = my_matches['matches']
    # sort matches by least recent
    my_matches.sort(key=lambda i: i['timestamp'])
    # populate database with match details 
    while len(my_matches) > 0:
        try:
            match_detail = APICall(call='match_detail',args={'region':region,'gameId':my_matches[0]['gameId']})
            print('getting match from', my_matches[0]['timestamp'])
            my_matches.pop(0)
            to_store = MatchHistory(time=int(match_detail['gameCreation']),data=json.dumps(match_detail),summoner=summoner,region=region)
            to_store.save()
        except Exception as e: print(e)

    match_detail = MatchHistory.objects.filter(summoner__iexact=summoner,region__iexact=region).order_by('-time')[:to_return]
    rax = []
    for i in range(len(match_detail)):
        rax.append(json.loads(match_detail[i].data))

    return rax

# I'm using these functions to standardize the objects I send to the template and to populate default values.
def textd(value='', style=''):# for generating text JSON objects for the template
    return {'value':str(value), 'style':style}

def imaged(url='https://www.freeiconspng.com/uploads/red-circular-image-error-0.png', width='30', height='30', onerror='', style='', title=''):# for generating image JSON objects for the template
    return {'url':url, 'width':width, 'height':height, 'onerror':onerror, 'title':title, 'style':style}

def oAuth(scope=''):
    cred=kroger_api_credentials
    headers={
            "Content-Type":"application/x-www-form-urlencoded",
            "Authorization": "Basic " + cred,
            }
    data={
        "grant_type": "client_credentials",
        "scope":scope
        #"scope": "product.compact"
        }
    r = requests.post(url="https://api.kroger.com/v1/connect/oauth2/token",headers=headers,data=data)
    return r.json()['access_token']

def APIKroger(url='',scope=''):
    try:
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + oAuth(scope=scope),
        }
        g = requests.get(url=url, headers=headers)
        to_store = APICallHistory(time=int(time.time()*1000),desc='a responsible api call',service='Kroger')
        return g.json()
    except Exception as e:
        print(e, ": Kroger API Error")
        return {'data':[]}

def processSizeMl(size='0 ml'):
    # going to consider the following size string patterns:
    # x bottles / y fl oz
    # x cans / y fl oz
    # x cans / y ml
    # x bottles / y ml
    # x ml
    # x fl oz
    # x l
    # not x cans.  Scuffed data is not my problem
    # this could be done gracefully with a regular expression but that would take longer
    rax = 0
    if 'oz' in size:
        if 'bottles /' in size:
            size = size.strip(' fl oz').replace(' bottles ', "").split('/')
            rax = float(size[0]) * float(size[1])
            rax *= 29.5735 # oz to ml conversion
        elif 'cans /' in size:
            size = size.strip(' fl oz').replace(' cans ', "").split('/')
            rax = float(size[0]) * float(size[1])
            rax *= 29.5735
        else:
            size = float(size.strip(' fl oz'))
            rax  = size * 29.5735
    elif 'ml' in size:
        if 'bottles /' in size:
            size = size.strip(' ml').replace(' bottles ', "").split('/')
            rax = float(size[0]) * float(size[1])
        elif 'cans /' in size:
            size = size.strip(' ml').replace(' cans ', "").split('/')
            rax = float(size[0]) * float(size[1])
        else:
            rax = float(size.strip(' ml'))
    elif ' l' in size:
        rax = float(size.strip(' l'))*1000
    else:
        print(size, "can't parse this")

    return rax
def getLocIds(zip='22903'):
    URL3 = 'https://api.kroger.com/v1/locations?filter.zipCode.near=22903'

    g = APIKroger(URL3)

    loc_id_list = []
    for location in g['data']:
        loc_id_list.append(location['locationId'])
    return loc_id_list

def updateProducts(loc_id_list=getLocIds()):
    loc_id_list.pop(0)
    loc_id_list.pop(0)
    print('updating products')
    load_data = json.loads(KrogerServiceData.objects.latest('time').data)
    brands = load_data['brands']
    abv_dict = load_data['abv_dict']
    products = {} # pid:desc
    price_size = {} # pdi:(lowest_price,cheapest_per_volume_size,price_per_ml_$)
    print(loc_id_list)
    for i in loc_id_list:
        print(brands)
        for brand in brands:
            start = 0
            URL4 = 'https://api.kroger.com/v1/products?filter.term=beer&filter.brand='+brand.replace(" ", "%20").replace("'", "%27").replace("&", "%26")+'&filter.locationId=' + i + \
                   '&filter.limit=50'
            g = APIKroger(url=URL4, scope="product.compact")
            while g['data'] != []:
                for product in g['data']:
                    ratios = []
                    for item in product['items']:
                        try: # not my fault if their data is fucked up
                            size = processSizeMl(item['size']) # float ml
                            price = 100
                            if item['price']['promo'] != 0:
                                price = item['price']['promo']
                            else:
                                price = item['price']['regular']
                            ratios.append((size / price, product['description'], item['size'], price))
                        except: # just going to ignore invalid or missing entries
                            print('DNE')
                    try:
                        optimal = max(ratios, key=lambda i: i[0])
                        price_size[product['productId']] = optimal
                    except Exception as e:
                        print('no ' + brand + " product found")
                    products[product['productId']] = product['description']
                start += 49
                URL4 = 'https://api.kroger.com/v1/products?filter.term=beer&filter.brand=' + brand.replace(" ", "%20").replace("'", "%27").replace("&", "%26") + '&filter.locationId=' \
                       + i + '&filter.limit=50&filter.start=' + str(start)
                g = APIKroger(url=URL4, scope="product.compact")

        diff = []
        for i in products.values():
            if i not in abv_dict.keys():
                #abv_dict[i] = input('input '+i+' abv: ')
                diff.append((i, abv_dict[i]))
                print(diff)

        for i in diff:
            print(',','"',i[0],'"', ':',i[1])
        data = []
        for key in price_size.keys():
            try:
                z = (price_size[key][0] * abv_dict[products[key]] * .01, price_size[key][1], price_size[key][2], price_size[key][3])
                data.append(z)
            except Exception as e: print(e, ': error transforming price_size data')
        # now price_size contains the dollars per ml of alcohol
        data.sort(reverse=True, key=lambda k:k[0])
        if data[:5] != []:
            to_store = KrogerServiceData(int(time.time()*1000), json.dumps({'brands':brands, 'abv_dict':abv_dict, 'products':products, 'price_size':price_size, 'loc_id_list':loc_id_list, 'cheapest5':data[:5]}))
            to_store.save()

        return (data[:5], diff)
# page-returning methods referenced in urls    
def test(request):
    tag = 'pogger'
    return render(request, 'personal/test.html', {'tag': tag})


def index_view(request):
    if request.method == 'POST':
        c = open("c.txt", "w")
        aeval = Interpreter(writer=c)

        try:
            torun = request.POST.get('torun')
            print(torun)
            aeval(torun)
            c.close()
            c = open("c.txt", "r")
            rax = '\n'
            rax = rax.join(c.readlines())
            return render(request, 'personal/index.html', {'error': '', 'return': str(rax)})
            c.close()
        except Exception as e:
            c.close()
            error = e
            return render(request, 'personal/index.html', {'error': str(e), 'return': ''})
        
        return render(request, 'personal/index.html', {'error': str(e), 'return': str(rax)})
        
        print("!")
        dest = request.POST['dest']
        return HttpResponseRedirect('/user/' + dest)

    return render(request, 'personal/index.html')

def code(request):
    return render(request, 'personal/codeSamples.html', {})
    
def profileView(request, profileID):
    profile_data = get_object_or_404(Profile, pk=profileID)
    return render(request, 'personal/profileview.html', {'profile_data': profile_data})

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        #if form.is_valid():
        ret = 'image uploaded as ' + handle_image_upload(request.FILES['image'],request.FILES['image'].name ,request.POST['iid'], request.POST['tags'])
        return render(request, 'personal/success.html', {'actionID': ret})
    else:
        form = UploadFileForm()
    return render(request, 'personal/upload.html', {'form': form})

def serveImage(request, image_ID):
    return render(request, 'personal/singleImage.html', {'imageID': image_ID})

def create_user(request):
    if request.method == 'POST':
        form = CreateNewProfileForm(request.POST, request.FILES)
        #if form.is_valid():
        ret = 'user created as ' + handle_create_new_user(request.FILES['resume'], request.POST['pid'], request.POST['pword'], request.POST['bio'], request.POST['dname'])
        return render(request, 'personal/success.html', {'actionID': ret})
    else:
        form = CreateNewProfileForm()
    return render(request, 'personal/createProfile.html', {'form': form})

def imageSearch(request):
    if request.method == 'POST':
        form = ImageSearchForm(request.POST, request.FILES)
            #if form.is_valid():
        iids = ImageFile.objects.filter(tags__contains=request.POST['tag'])
        return render(request, 'personal/imageSearch.html', {'iids': iids})
    else:
        form = ImageSearchForm()
    return render(request, 'personal/imageSearch.html', {'form': form})

def riotDashboard(request):
    dd = LolWatcher('RGAPI_fake')#fake api key for dd calls which do not require it

    region = 'na1'

    summoner = "Small_Crawler"
    summoner_clean = "Small Crawler"

    match_details = updateMatchHistory(summoner=summoner,to_return=10)# call to api request manager
    match_detail = match_details[0]

    history = [] # list of data dicts
    entryid = 0
    
    wins = 0
    losses = 0

    # check league's latest version
    latest = dd.data_dragon.versions_for_region(region)['n']['champion']
    # Lets get some champions static information, dd calls
    static_item_list = dd.data_dragon.items(latest, 'en_US')
    static_champ_list = dd.data_dragon.champions(latest, False, 'en_US')
    static_spell_list = dd.data_dragon.summoner_spells(latest, 'en_US')

    # champ static list data to dict for looking up champion names
    champ_dict = {}
    for key in static_champ_list['data']:
        row = static_champ_list['data'][key]
        champ_dict[row['key']] = row['id']

        
    # to convert from item id to name
    item_dict = static_item_list['data']
    for key in item_dict:
        item_dict[key] = item_dict[key]['name']

    # to convert from spell id to spell name
    static_spell_list = watcher.data_dragon.summoner_spells(latest, 'en_US')
    static_spell_list = static_spell_list['data']
    spell_dict = {}
    for key in static_spell_list:
        spell_dict[static_spell_list[key]['key']] = static_spell_list[key]['id']

    static_runes_list = watcher.data_dragon.runes_reforged(latest)
    static_runes_list = watcher.data_dragon.runes_reforged(latest, 'en_US')
    rune_dict = {}
    for style in static_runes_list:
        for rune in style['slots'][0]['runes']:
            rune_dict[rune['id']] = rune['icon']


    for match_detail in match_details:
        #data = {header: summoner scoreline, content: entire scoreboard, entryId: games since most recent}
        data = {'header':[], 'content':[]}
        # we'll be using this dataframe to organize and manipulate the data we will send to the page
        participants = []
        for row in match_detail['participants']:
            participants_row = {}
            participants_row['champion'] = row['championId']
            participants_row['spell1'] = row['spell1Id']
            participants_row['spell2'] = row['spell2Id']
            participants_row['win'] = row['stats']['win']
            participants_row['kills'] = row['stats']['kills']
            participants_row['deaths'] = row['stats']['deaths']
            participants_row['assists'] = row['stats']['assists']
            participants_row['totalDamageDealt'] = row['stats']['totalDamageDealt']
            participants_row['goldEarned'] = row['stats']['goldEarned']
            participants_row['champLevel'] = row['stats']['champLevel']
            participants_row['totalMinionsKilled'] = row['stats']['totalMinionsKilled']
            participants_row['item0'] = row['stats']['item0']
            participants_row['item1'] = row['stats']['item1']
            participants_row['item2'] = row['stats']['item2']
            participants_row['item3'] = row['stats']['item3']
            participants_row['item4'] = row['stats']['item4']
            participants_row['item5'] = row['stats']['item5']
            participants_row['keystone_path'] = rune_dict[row['stats']['perk0']]
            participants.append(participants_row)
    

        #fixing the dataframe
        new_col = []

        for summoner in match_detail['participantIdentities']:
            new_col.append(summoner['player']['summonerName'])
        new_col = pd.DataFrame(new_col, columns=['summonerName'])

        for row in participants:
            row['championName'] = champ_dict[str(row['champion'])]

        df = pd.DataFrame(participants)
        df['summonerName'] = new_col

        lab = list(df.columns)

        # not using this right now, but I may want it later
        score_headline = {'team100':{'kills':sum(df['kills'][:5]),'deaths':sum(df['deaths'][:5]),'assists':sum(df['assists'][:5])},
                         'team200':{'kills':sum(df['kills'][5:]),'deaths':sum(df['deaths'][5:]),'assists':sum(df['assists'][5:])}}
        
        team100KDA = str(score_headline['team100']['kills']) + '/' + str(score_headline['team100']['deaths']) + '/' + str(score_headline['team100']['assists'])
        team200KDA = str(score_headline['team200']['kills']) + '/' + str(score_headline['team200']['deaths']) + '/' + str(score_headline['team200']['assists'])

        team100Gold = str(sum(df['goldEarned'][:5]))
        team200Gold = str(sum(df['goldEarned'][5:]))

        for index, row in df.iterrows():
            if index == 0:
                data['content'].append({'text':[textd(match_detail['teams'][0]['win'].replace('Fail','Loss')), textd(team100KDA), textd('Gold Earned: ' + team100Gold)], 'images':[]})
            if index == 5:
                data['content'].append({'text':[textd(match_detail['teams'][1]['win'].replace('Fail','Loss')), textd(team200KDA), textd('Gold Earned: ' + team200Gold)], 'images':[]})
            l = copy(lab) # my understanding of python is lacking, because idk why I have to do this sometimes
            # sometimes she choses to pass something by reference instead of value

            line = {}
            for i in row: # this is inefficient, but truly the time it took to write this comment is more than changing it will ever save
                line[l[0]] = i
                l.pop(0)

            stats = {'text':[], 'images':[], 'bgcolor':'gray'} # list of textds and imageds to be displayed on page and their bg color

            stats['images'].append(imaged('http://ddragon.leagueoflegends.com/cdn/img/' + line['keystone_path']))
            stats['images'].append(imaged(url = 'http://ddragon.leagueoflegends.com/cdn/10.13.1/img/champion/' + line['championName'] + '.png', width=50, height=50,title=line['championName']))
            stats['images'].append(imaged(url='https://i.imgur.com/Z4PgTUN.png'))
            try: # bots do not take summoner spells
                stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/spell/' + spell_dict[str(int(line['spell1']))] + '.png'))
                stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/spell/' + spell_dict[str(int(line['spell2']))] + '.png'))
            except:
                pass
            stats['images'].append(imaged(url='https://i.imgur.com/Z4PgTUN.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item0'])) + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item1'])) + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item2'])) + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item3'])) + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item4'])) + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item5'])) + '.png'))
            if line['win'] == True:
                if line['summonerName'] == summoner_clean:
                    wins += 1
            else:
                if line['summonerName'] == summoner_clean:
                    losses += 1
            stats['text'].append(textd(value=str(line['kills'])+'/'+str(line['deaths'])+'/'+str(line['assists'])))
            stats['text'].append(textd(value=line['summonerName']))#summoner name
            
            if line['summonerName'] == summoner_clean:
                data['header'] = copy(stats)
                if line['win'] == True:
                    data['header']['text'].append(textd(style='color:green;', value='Win'))
                else:
                    data['header']['text'].append(textd(style='color:red;', value='Loss'))

                data['entryId'] = entryid
                entryid += 1
                stats['bgcolor'] = 'gold'
            else:
                stats['bgcolor'] = 'gray'

            data['content'].append(stats)

        history.append(data)

    return render(request, 'personal/dashboard.html', {'history':history, 'wl':{'wins':wins, 'losses':losses}})

def krogerDashboard(request):
    try:
        data = json.loads(KrogerServiceData.objects.latest('time').data)['cheapest5']
    except:
        data = []
    return render(request, 'personal/test.html', {'data':data})

def resume(request):
    return render(request, 'personal/resume.html')

def ide(request):
    if request.method == 'POST':
        c = open("c.txt", "w")
        aeval = Interpreter(writer=c)

        try:
            torun = request.POST.get('torun')
            print(torun)
            aeval(torun)
            c.close()
            c = open("c.txt", "r")
            rax = '\n'
            rax = rax.join(c.readlines())
            return render(request, 'personal/ide.html', {'error': '', 'return': str(rax)})
            c.close()
        except Exception as e:
            c.close()
            error = e
            return render(request, 'personal/ide.html', {'error': str(e), 'return': ''})
        
        return render(request, 'personal/ide.html', {'error': str(e), 'return': str(rax)})
    return render(request, 'personal/ide.html')