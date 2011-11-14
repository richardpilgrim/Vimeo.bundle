import re, string

VIMEO_NAMESPACE   = {'atom':'http://www.w3.org/2005/Atom', 'media':'http://search.yahoo.com/mrss/'}
VIMEO_URL         = 'http://vimeo.com'
VIMEO_LOAD_CLIP   = 'http://vimeo.com/moogaloop/load/clip:%s/local?param_md5=0&param_context_id=&param_force_embed=0&param_clip_id=3715286&param_show_portrait=0&param_multimoog=&param_server=vimeo.com&param_show_title=0&param_color=00ADEF&param_autoplay=0&param_show_byline=0&param_fullscreen=1&param_context=subscriptions|newest&param_force_info=undefined&context=subscriptions'
VIMEO_PLAY_CLIP   = 'http://vimeo.com/moogaloop/play/clip:%s/%s/%s/?q=%s&type=local'
VIMEO_DIRECTORY   = 'http://vimeo.com/%s/%s/page:%d'
VIMEO_SEARCH      = 'http://vimeo.com/search/videos/search:%s/st/%s/page:%d/sort:plays/format:detail'

ICON = 'icon-default.jpg'
ART = 'art-default.jpg'

####################################################################################################
def Start():
  Plugin.AddPrefixHandler('/video/vimeo', MainMenu, 'Vimeo', ICON, ART)
  Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
  ObjectContainer.title1 = 'Vimeo'
  ObjectContainer.content = ContainerContent.GenericVideos
  ObjectContainer.art = R(ART)
  DirectoryObject.thumb = R(ICON)
  HTTP.CacheTime = 1800

####################################################################################################
def MainMenu():
  oc = ObjectContainer(
    objects = [
      DirectoryObject(
        key     = Callback(GetMyStuff),
        title   = L('My Stuff')
      ),
      DirectoryObject(
        key     = Callback(GetVideosRSS, url='/channels/staffpicks/videos', title2='Staff Picks'),
        title   = L('Staff Picks'),
        thumb   = R('staffpicks.png')
      ),
      DirectoryObject(
        key     = Callback(FeaturedChannels),
        title   = L('Featured Channels'),
        thumb   = R('featured.png')
      ),
      DirectoryObject(
        key     = Callback(GetVideosRSS, url='/channels/hd/videos', title2='High Def'),
        title   = L('High Def'), 
        thumb   = R('hd.png')
      ),
      DirectoryObject(
        key     = Callback(Categories, noun='channels', url='all'),
        title   = L('Channels'), 
        thumb   = R('channels.png')
      ),
      DirectoryObject(
        key     = Callback(Categories, noun='groups', url='all', sort='members'),
        title   = L('Groups'), 
        thumb   = R('groups.png')
      ),
      InputDirectoryObject(
        key     = Callback(Search),
        title   = L('Search'),
        prompt  = L('Search for Videos'),
        thumb   = S('search.png')
      ),
      PrefsObject(
        title   = L('Preferences...'),
        thumb   = R('prefs.png')
      )
    ]
  )

  return oc

####################################################################################################
def GetMyStuff():

  # See if we need to log in.
  xml = HTML.ElementFromURL(VIMEO_URL + '/subscriptions/channels/sort:name', cacheTime=0)
  if xml.xpath('//title')[0].text != 'Your subscriptions on Vimeo':
    # See if we have any creds stored.
    if not Prefs['email'] and not Prefs['password']:
      return MessageContainer(header='Logging in', message='Please enter your email and password in the preferences.')
    # Try to log in
    Login()
    Log(xml.xpath('//title')[0].text)

    # Now check to see if we're logged in.
    xml = HTML.ElementFromURL(VIMEO_URL + '/subscriptions/channels/sort:name', cacheTime=0)
    if xml.xpath('//title')[0].text != 'Your subscriptions on Vimeo':
      return MessageContainer(header='Error logging in', message='Check your email and password in the preferences.')

  user = xml.xpath('.//a[@class="label" and text()="Me"]')[0].get('href')[1:]
  oc = ObjectContainer()

  oc.add(DirectoryObject(
    key = Callback(GetVideosRSS, url='/'+user+'/videos', title2=L('My Videos')),
    title = 'My Videos'
  ))

  oc.add(DirectoryObject(
    key = Callback(GetVideosRSS, url='/'+user+'/likes', title2=L('My Likes')),
    title = 'My Likes'
  ))

  oc.add(DirectoryObject(
    key = Callback(GetDirectory, noun=user, url='groups', sort='name', narrow='joined'),
    title = L('My Groups')
  ))

  oc.add(DirectoryObject(
    key = Callback(GetDirectory, noun=user, url='channels', sort='name', narrow='subscribe'),
    title = L('My Channels')
  ))

  oc.add(DirectoryObject(
    key = Callback(GetContacts, url='/'+user+'/contacts', title2='My Contacts'),
    title = L('My Contacts')
  ))

  return oc

####################################################################################################
def GetContacts(url, title2=None):
  oc = ObjectContainer(title2=title2, view_group='InfoList')

  url += '/sort:name'
  for contact in HTML.ElementFromURL(VIMEO_URL + url).xpath('//div[@class="contact"]'):
    thumb = contact.find('img').get('src')
    title = contact.xpath('./div[@class="deleter"]')[0].xpath('./span[@class="greyd"]')[0].text

    info = contact.xpath('./div/div[@class="info"]')[0]
    try:
      subtitle = info.xpath('./div[@class="location"]')[0].text + "\n"
    except:
      subtitle = ""
    subtitle += info.xpath('./div[@class="date"]')[0].text

    summary = '\n'
    try:
      summary += info.xpath('./a[@class="contacts"]')[0].text + ", "
    except:
      pass

    try:
      summary += info.xpath('./a[@class="videos"]')[0].text
      url = info.xpath('./a[@class="videos"]')[0].get('href')
      oc.add(DirectoryObject(
        key = Callback(GetVideosRSS, url=url, title2=title),
        title = title,
        tagline = subtitle,
        thumb = thumb,
        summary = summary,
      ))
    except:
      # Doesn't have any videos for some reason... skip
      pass

  return oc

####################################################################################################
def FeaturedChannels():
  oc = ObjectContainer(title2=L('Featured Channels'), view_group='InfoList')

  for c in HTML.ElementFromURL(VIMEO_URL + '/channels').xpath("//div[@class='badge']"):
    title = c.find('a').get('title')
    thumb = re.findall("'(.*)'", c.get('style'))[0]
    url = c.find('a').get('href')
    url = url[url.rfind('/')+1:]

    oc.add(DirectoryObject(
      key = Callback(GetVideosRSS, url='/channels/'+url+'/videos', title2=title),
      title = title,
      thumb = thumb
    ))

  return oc

####################################################################################################
def Categories(noun, url, sort='subscribed'):
  oc = ObjectContainer(title2=L('Channels'), view_group='InfoList')

  for category in HTML.ElementFromURL(VIMEO_URL + '/channels').xpath('//div[@id="cloud"]/ul/li'):
    title = string.capwords(category.find('a').text)
    subtitle = category.find('span').text + ' ' + noun
    cat = category.find('a').get('href')
    cat = cat[cat.find(':')+1:]

    oc.add(DirectoryObject(
      key = Callback(GetDirectory, category=cat, noun=noun, url=url, sort=sort, title2=title),
      title = title,
      tagline = subtitle,
    ))

  return oc

####################################################################################################
def GetDirectory(category=None, noun=None, url=None, page=1, sort='subscribed', narrow=None, title2=None):
  oc = ObjectContainer(title2=title2, view_group='InfoList', replace_parent=(page > 1))

  the_url = VIMEO_DIRECTORY % (noun, url, page)
  if category is not None:
    the_url += '/category:%s' % category
  if sort is not None:
    the_url += '/sort:%s' % sort
  if narrow is not None:
    the_url += '/narrow:%s' % narrow

  if url == 'channels' and narrow is not None:
    xpath = '//ul[@id="channel_listing"]/li'
    xp_title = './div[@class="digest"]/div[@class="channel_title"]/a'
    xp_subtitle = './div[@class="digest"]/div[@class="counts"]'
    xp_desc = './div[@class="digest"]/div[@class="descrip"]'
    full_subtitle = True
    noun = 'channels'
    sort = 'newest'
  elif url == 'groups' and narrow is not None:
    xpath = '//ul[@id="group_listing"]/li'
    xp_title = './div[@class="digest"]/div[@class="group_title"]/a'
    xp_subtitle = './div[@class="digest"]/div[@class="counts"]'
    xp_desc = './div[@class="digest"]/div[@class="descrip"]'
    full_subtitle = True
    noun = 'groups'
  else:
    xpath = '//div[@class="item last"]'
    xp_title= './div/div[@class="title"]/a'
    xp_subtitle = './div/div[@class="date"]'
    xp_desc = './div/div[@class="description"]'
    full_subtitle = False

  for channel in HTML.ElementFromURL(the_url).xpath(xpath):
    title = channel.xpath(xp_title)[0].text
    subtitle_items = [e for e in channel.xpath(xp_subtitle)[0].itertext()]
    subtitle = "".join(subtitle_items[0:1]).strip()
    if len(subtitle) == 0 or full_subtitle == True:
      subtitle = "".join(subtitle_items).strip()
    try: desc = channel.xpath(xp_desc)[0].text
    except: desc =''
    link = channel.xpath('./div[@class="channel_thumb"]/a')[0]
    thumb = link.find('img').get('src')
    channel = link.get('href')
    channel = channel[channel.rfind('/')+1:]
    
    oc.add(DirectoryObject(
      key = Callback(GetVideosRSS, url='/'+noun+'/'+channel+'/videos', title2=title),
      title = title,
      tagline = subtitle,
      summary = desc,
      thumb = thumb 
    ))

  oc.add(DirectoryObject(
    key = Callback(GetDirectory, category=category, noun=noun, url=url, sort=sort, narrow=narrow, page=page+1, title2=title2),
    title = L('More...'),
  ))

  return oc

####################################################################################################
def Search(query, page=1):
  oc = ObjectContainer(title2=L('Search Results'), view_group='InfoList', replace_parent=(page > 1))
  query = query.replace(' ', '+')
  
  # Need to get the security token.
  vimeo_page = HTML.ElementFromURL(VIMEO_URL, cacheTime=0)
  security_token = vimeo_page.xpath('.//input[@id="xsrft"]')[0].get('value')[0:8]
  
  vimeo_html = HTTP.Request(VIMEO_SEARCH % (query, security_token, page), headers={"Cookie" : "searchtoken="+security_token}).content

  for result in HTML.ElementFromString(vimeo_html).xpath('//div[@class="item last"]'):
    title = result.xpath('./div/div[@class="title"]/a')[0].text
    subtitle_items = [e.strip() for e in result.xpath('./div/div[@class="date"]')[0].itertext()]
    subtitle = "%s (%s plays)" % (subtitle_items[0], subtitle_items[2])
    try: desc = result.xpath('./div/div[@class="description"]')[0].text
    except: desc =''
    try:
        link = result.xpath('./div[@class="thumbnail_box"]/a[@class="thumbnail"]')[0]
        thumb = link.find('img').get('src')
        url = 'http://vimeo.com' + link.get('href')
    except:
        PMS.Log(XML.StringFromElement(result))
        continue
    #
    oc.add(VideoClipObject(
      title = title,
      tagline = subtitle,
      summary = desc,
      thumb = thumb,
      url = url
    ))
    
  oc.add(DirectoryObject(
    key = Callback(Search, query=query, page=page+1),
    title = L('More...')
  ))
  return oc


####################################################################################################
def GetVideosRSS(url, title2):
#  oc = ObjectContainer(title2=title2, http_cookies=HTTP.CookiesForURL(VIMEO_URL), view_group='InfoList')
  oc = ObjectContainer(title2=title2, view_group='InfoList')

  for video in XML.ElementFromURL(VIMEO_URL + url + '/rss', errors="ignore").xpath('//item', namespaces=VIMEO_NAMESPACE):
    title = video.find('title').text
    date = Datetime.ParseDate(video.find('pubDate').text).strftime('%a %b %d, %Y')
    desc = HTML.ElementFromString(video.find('description').text)
    try:
      thumb = video.xpath('./media:content/media:thumbnail', namespaces=VIMEO_NAMESPACE)[0].get('url')
      key = video.xpath('./media:content/media:player', namespaces=VIMEO_NAMESPACE)[0].get('url')
      key = key[key.rfind('=')+1:]
      summary = String.StripTags(video.find('description').text)

      url = 'http://vimeo.com/%s' % key

      oc.add(VideoClipObject(
        title = title,
        summary = summary,
        thumb = thumb,
        url = url
      ))
    except:
      Log('Failed to load video: %s' % title)
      pass

  return oc

####################################################################################################
def GetThumb(url):
  try:
    data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
    return DataObject(data, 'image/jpeg')
  except:
    pass

  return Redirect(R(ICON))

####################################################################################################
def Login():
  xsrft = HTML.ElementFromURL('https://secure.vimeo.com/log_in', cacheTime=0).xpath('//input[@id="xsrft"]')[0].get('value')

  values = {
     'sign_in[email]' : Prefs['email'],
     'sign_in[password]' : Prefs['password'],
     'token' : xsrft
  }

  headers = {
     'Cookie' : 'xsrft=%s' % xsrft
  }

  x = HTTP.Request('https://secure.vimeo.com/log_in', values, headers).content
