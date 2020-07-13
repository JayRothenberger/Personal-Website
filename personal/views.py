import time
import json

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.db.models import Max

from .models import Profile, ImageFile, MatchDetail, MatchHistory, APICallHistory, APIKey
from .forms import UploadFileForm, CreateNewProfileForm, ImageSearchForm
from .filesystem import handle_image_upload, handle_create_new_user

from riotwatcher import LolWatcher, ApiError
import pandas as pd
from asteval import Interpreter

#globals
try:
    api_key = APIKey.objects.latest('time').key #this should come from db in production
    watcher = LolWatcher(api_key)
except:
    pass

# class declarations


# non-page returning helper methods
#api call manager so we don't exceed the call limit
def APICall(call='matchlist_by_account', args={'summoner':'Small_Crawler', 'region':'na1'}):
    try:
        history = APICallHistory.objects.all().order_by('-time')
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
        latest_detail = MatchHistory.objects.latest('time')
        begin = latest_detail.time + 1
    except Exception as e: # if there happens to be no object
        print(e, 'could not get latest detail time')
        begin = 0

    me = APICall(call='summoner_by_name',args={'summoner':summoner,'region':region})
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
    return {'value':value, 'style':style}

def imaged(url='https://www.freeiconspng.com/uploads/red-circular-image-error-0.png', width='30', height='30', onerror='', style='', title=''):# for generating image JSON objects for the template
    return {'url':url, 'width':width, 'height':height, 'onerror':onerror, 'title':title, 'style':style}

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

    history = []
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

    for match_detail in match_details:
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

        for index, row in df.iterrows():
            l = []
            for i in lab: # my understanding of python is lacking, because idk why I have to do this sometimes
                l.append(i) # sometimes she choses to pass something by reference instead of value

            line = {}
            for i in row:
                line[l[0]] = i
                l.pop(0)
            stats = {'text':[], 'images':[]}
            stats['images'].append(imaged(url = 'http://ddragon.leagueoflegends.com/cdn/10.13.1/img/champion/' + line['championName'] + '.png', width=50, height=50))
            stats['images'].append(imaged(url='https://i.imgur.com/Z4PgTUN.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/spell/' + spell_dict[str(int(line['spell1']))] + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/spell/' + spell_dict[str(int(line['spell2']))] + '.png'))
            stats['images'].append(imaged(url='https://i.imgur.com/Z4PgTUN.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item0'])) + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item1'])) + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item2'])) + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item3'])) + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item4'])) + '.png'))
            stats['images'].append(imaged(url='http://ddragon.leagueoflegends.com/cdn/10.13.1/img/item/' + str(int(line['item5'])) + '.png'))
            if line['win'] == True:
                stats['text'].append(textd(style='color:green;', value='Win'))
                if line['summonerName'] == summoner_clean:
                    wins += 1
            else:
                stats['text'].append(textd(style='color:red;', value='Loss'))
                if line['summonerName'] == summoner_clean:
                    losses += 1
            stats['text'].append(textd(value=str(line['kills'])+'/'+str(line['deaths'])+'/'+str(line['assists'])))
            stats['text'].append(textd(value=line['summonerName']))#summoner name
            data['content'].append(stats)
            if line['summonerName'] == summoner_clean:
                data['header'] = stats
                data['entryId'] = entryid
                entryid += 1
        history.append(data)

    #lets try getting the pictures next for the items and champions
    return render(request, 'personal/dashboard.html', {'history':history, 'wl':{'wins':wins, 'losses':losses}})