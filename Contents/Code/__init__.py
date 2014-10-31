VIMEO_NAMESPACE = {'media':'http://search.yahoo.com/mrss/'}

VIMEO_URL = 'https://vimeo.com'
#VIMEO_SEARCH = '%s/search/page:%%d/sort:relevant/format:detail?q=%%s' % VIMEO_URL
VIMEO_CATEGORIES = '%s/categories' % VIMEO_URL

VIMEO_FEATURED_CHANNELS = '%s/channels/page:%%d/sort:subscribers' % VIMEO_URL

VIMEO_CATEGORY_CHANNELS = '%s/categories/%%s/channels/page:%%%%d/sort:subscribers/format:detail' % VIMEO_URL
VIMEO_CATEGORY_GROUPS = '%s/categories/%%s/groups/page:%%%%d/sort:members/format:detail' % VIMEO_URL

VIMEO_CHANNEL = '%s/channels/%%s/videos/page:%%%%d/sort:preset/format:detail' % VIMEO_URL
VIMEO_GROUP = '%s/groups/%%s/videos/page:%%%%d/sort:date/format:detail' % VIMEO_URL

# My Stuff
VIMEO_MY_VIDEOS = '%s/%%s/videos/page:%%%%d/sort:date/format:detail' % VIMEO_URL
VIMEO_MY_LIKES = '%s/%%s/likes/page:%%%%d/sort:date/format:detail' % VIMEO_URL
VIMEO_MY_CHANNELS = '%s/%%s/channels/page:%%%%d/sort:alphabetical/format:detail' % VIMEO_URL
VIMEO_MY_GROUPS = '%s/%%s/groups/page:%%%%d/sort:alphabetical/format:detail' % VIMEO_URL
VIMEO_FOLLOWING = '%s/%%s/following/page:%%%%d/sort:alphabetical/format:detail' % VIMEO_URL
VIMEO_WATCH_LATER = '%s/home/watchlater/page:%%d/sort:date/format:detail' % VIMEO_URL

# Site
RE_TOKEN = Regex("xsrft:(\s*)'(?P<xsrft>[^']+)'")

# RSS
RE_MEDIA_CATEGORY = Regex('<media:category.+?<\/media:category>')
RE_CONTROL_CHARS = Regex(u'[\u0000-\u001F]')
RE_SUMMARY = Regex('(<p class="first">.*</p>)', Regex.DOTALL)

####################################################################################################
def Start():

	ObjectContainer.title1 = 'Vimeo'
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'

####################################################################################################
@handler('/video/vimeo', 'Vimeo')
def MainMenu():

	oc = ObjectContainer(
		objects = [
			DirectoryObject(
				key		= Callback(GetMyStuff, title=L('My Stuff')),
				title	= L('My Stuff')
			),
			DirectoryObject(
				key		= Callback(GetVideos, title=L('Staff Picks'), url=VIMEO_CHANNEL % 'staffpicks'),
				title	= L('Staff Picks'),
				summary	= L('Hand-picked videos we like.')
			),
			DirectoryObject(
				key		= Callback(GetDirectory, title=L('HD'), url=VIMEO_CATEGORY_CHANNELS % 'hd'),
				title	= L('HD'),
				summary	= L('Amazing HD quality videos for you.')
			),
			DirectoryObject(
				key		= Callback(GetDirectory, title=L('Featured Channels'), url=VIMEO_FEATURED_CHANNELS),
				title	= L('Featured Channels')
			),
			DirectoryObject(
				key		= Callback(Categories, title=L('Channels'), directory_type='channels'),
				title	= L('Channels'),
				summary	= L('Video showcases curated by members.')
			),
			DirectoryObject(
				key		= Callback(Categories, title=L('Groups'), directory_type='groups'),
				title	= L('Groups'),
				summary	= L('Join other members to watch and discuss.')
			),
#			InputDirectoryObject(
#				key		= Callback(Search),
#				title	= L('Search'),
#				prompt	= L('Search for Videos')
#			),
			PrefsObject(
				title	= L('Preferences...'),
			)
		]
	)

	return oc

####################################################################################################
@route('/video/vimeo/{directory_type}/categories')
def Categories(title, directory_type):

	oc = ObjectContainer(title2=title)

	for category in HTML.ElementFromURL(VIMEO_CATEGORIES).xpath('//ul[@id="categories"]/li/a'):
		title = category.xpath('./h2/text()')[0]
		category_id = category.get('href').rsplit('/',1)[1]

		if directory_type == 'channels':
			url = VIMEO_CATEGORY_CHANNELS % category_id
		elif directory_type == 'groups':
			url = VIMEO_CATEGORY_GROUPS % category_id

		oc.add(DirectoryObject(
			key = Callback(GetDirectory, title=title, url=url),
			title = title
		))

	return oc

####################################################################################################
@route('/video/vimeo/directory', page=int)
def GetDirectory(title, url, page=1):

	oc = ObjectContainer(title2=title)
	html = HTML.ElementFromURL(url % page)

	for el in html.xpath('//ol[contains(@class, "browse")]/li'):

		# It appears that some items can be removed and replaced with a placeholder. If this is the
		# case, it will not have an <a> node and therefore we should ignore it an move on.
		try: el_url = el.xpath('.//a')[0].get('href')
		except: continue

		(junk, directory_type, el_id) = el_url.split('/')

		if directory_type == 'channels':
			el_url = VIMEO_CHANNEL % el_id
		elif directory_type == 'groups':
			el_url = VIMEO_GROUP % el_id

		el_title = ''.join(el.xpath('.//p[@class="title"]//text()')).strip()
		el_thumb = el.xpath('.//img')[0].get('src').replace('_150.jpg', '_640.jpg')

		try: el_summary = el.xpath('.//p[@class="description"]/text()')[0].strip()
		except: el_summary = ''

		oc.add(DirectoryObject(
			key = Callback(GetVideos, title=el_title, url=el_url),
			title = el_title,
			summary = el_summary,
			thumb = Resource.ContentsOfURLWithFallback(el_thumb)
		))

	if len(html.xpath('//a[@rel="next"]')) > 0:
		oc.add(NextPageObject(
			key = Callback(GetDirectory, title=title, url=url, page=page+1),
			title = L('More...')
		))

	# It appears that sometimes we expect another page, but there ends up being no valid videos available
	if len(oc) == 0 and page > 1:
		return ObjectContainer(header = "No More Videos", message = "No more videos are available...")

	return oc

####################################################################################################
@route('/video/vimeo/videos', page=int, cacheTime=int, allow_sync=True)
def GetVideos(title, url, page=1, cacheTime=CACHE_1HOUR, ajaxRequest = False):

	oc = ObjectContainer(title2=title)

	if not url.startswith('http'):
		url = '%s/%s' % (VIMEO_URL, url)

	if ajaxRequest:
		HTTP.Headers['X-Requested-With'] = 'XMLHttpRequest'
		
	html = HTML.ElementFromURL(url % page, cacheTime=cacheTime)
	results = {}

	@parallelize
	def GetAllVideos():
		videos = html.xpath('//ol[contains(@class, "browse")]/li')

		for num in range(len(videos)):
			video = videos[num]

			@task
			def GetVideo(num=num, video=video, results=results):
				if len(video.xpath('.//div[contains(@class, "private")]')) > 0 or len(video.xpath('.//span[@class="processing"]')) > 0:
					return

				# It appears that some videos are still actually 'private' or only available if the user has authenticated. The easiest, 
				# but slightly hacky way, is to simply grab the actual page and see whats there. We're normally only handling a 'few' pages
				# so this shouldn't take too long. Although, i'm not that pleased that we have to do it :(
				video_id = video.xpath('.//a')[0].get('href').rsplit('/',1)[1]
				url = '%s/%s' % (VIMEO_URL, video_id)

				try:
					page = HTML.ElementFromURL(url, cacheTime=CACHE_1WEEK)
					Log(HTML.StringFromElement(page, encoding='utf8'))

					if len(page.xpath('//header[@id = "page_header"]//h1[contains(text(), "Private Video")]')) > 0:
						return

					video_title = video.xpath('.//p[@class="title"]/a/text()')[0].strip()
					video_summary = video.xpath('.//p[@class="description"]/text()')[0].strip()
					video_duration = TimeToMs(video.xpath('.//div[@class="duration"]/text()')[0])
					video_thumb = video.xpath('.//img')[0].get('src').replace('_150.jpg', '_640.jpg')

					results[num] = VideoClipObject(
						url = url,
						title = video_title,
						summary = video_summary,
						duration = video_duration,
						thumb = Resource.ContentsOfURLWithFallback(video_thumb)
					)

				except:
					return

	keys = results.keys()
	keys.sort()

	for key in keys:
		oc.add(results[key])

	if len(html.xpath('//a[@rel="next"]')) > 0:
		oc.add(NextPageObject(
			key = Callback(GetVideos, title=title, url=url, page=page+1, cacheTime=cacheTime),
			title = L('More...')
		))

	# It appears that sometimes we expect another page, but there ends up being no valid videos available
	if len(oc) == 0 and page > 1:
		return ObjectContainer(header = "No More Videos", message = "No more videos are available...")

	if ajaxRequest:
		del HTTP.Headers['X-Requested-With']
		
	return oc

####################################################################################################
@route('/video/vimeo/videos/rss')
def GetVideosRSS(url, title):

	oc = ObjectContainer(title2=title)

	if not url.startswith('http'):
		url = '%s/%s' % (VIMEO_URL, url)

	# Deal with non utf-8 character problem by removing the <media:category> element before parsing the document as XML
	xml = HTTP.Request(url).content
	xml = RE_MEDIA_CATEGORY.sub('', xml)

	# Remove any control characters, yucky fix :|
	# http://stackoverflow.com/questions/3748855/how-do-i-specify-a-range-of-unicode-characters-in-a-regular-expression-in-python
	# http://www.unicode.org/charts/PDF/U0000.pdf
	xml = RE_CONTROL_CHARS.sub('', xml)

	results = {}

	@parallelize
	def GetAllVideos():
		videos = XML.ElementFromString(xml).xpath('//item')

		for num in range(len(videos)):
			video = videos[num]

			@task
			def GetVideo(num=num, video=video, results=results):
				title = video.xpath('./title')[0].text.strip()
				date = Datetime.ParseDate(video.xpath('./pubDate')[0].text).date()

				try:
					summary = video.xpath('./description')[0].text.replace('\n', '').replace('<br>', '<br />')
					summary = RE_SUMMARY.search(summary).group(1)
					summary = summary.split('<strong>')[0]
					summary = HTML.ElementFromString(summary).xpath('//text()')
					summary = '\n'.join(summary)
				except:
					summary = ''

				try:
					thumb = video.xpath('./media:content/media:thumbnail', namespaces=VIMEO_NAMESPACE)[0].get('url').replace('_200.jpg', '_640.jpg')
				except:
					thumb = None

				try:
					key = video.xpath('./media:content/media:player', namespaces=VIMEO_NAMESPACE)[0].get('url')
					key = key[key.rfind('=')+1:]
					url = '%s/%s' % (VIMEO_URL, key)

					if 'video' in JSON.ObjectFromURL('http://player.vimeo.com/config/%s' % key, cacheTime=CACHE_1WEEK):
						results[num] = VideoClipObject(
							title = title,
							summary = summary,
							thumb = Resource.ContentsOfURLWithFallback(thumb),
							originally_available_at = date,
							url = url
						)
					else:
						Log(' --> Video is private: %s - http://vimeo.com/%s' % (title, key))

				except:
					Log(' --> Failed to load video: %s' % title)
					pass

	keys = results.keys()
	keys.sort()

	for key in keys:
		oc.add(results[key])

	return oc

####################################################################################################
@route('/video/vimeo/videos/my_subscriptions', allow_sync=True)
def GetMySubscriptions(title):

	rss_url = HTML.ElementFromURL(VIMEO_URL).xpath('//a[contains(@title, "My Subscriptions RSS")]')[0].get('href')
	return GetVideosRSS(url=rss_url, title=title)

####################################################################################################
@route('/video/vimeo/my_stuff')
def GetMyStuff(title):

	# See if we need to log in
	if not LoggedIn():
		# See if we have any creds stored
		if not Prefs['email'] or not Prefs['password']:
			return ObjectContainer(header=L('Logging in'), message=L('Please enter your email and password in the preferences.'))

		# Try to log in
		Login()

		# Now check to see if we're logged in
		if not LoggedIn():
			return ObjectContainer(header=L('Error logging in'), message=L('Check your email and password in the preferences.'))

	user = GetUsername()

	oc = ObjectContainer(
		title2 = title,
		objects = [
			DirectoryObject(
				key		= Callback(GetVideos, title=L('My Videos'), url=VIMEO_MY_VIDEOS % user, cacheTime=300),
				title	= L('My Videos')
			),
			DirectoryObject(
				key		= Callback(GetVideos, title=L('My Likes'), url=VIMEO_MY_LIKES % user, cacheTime=300),
				title	= L('My Likes')
			),
			DirectoryObject(
				key		= Callback(GetDirectory, title=L('My Channels'), url=VIMEO_MY_CHANNELS % user),
				title	= L('My Channels')
			),
			DirectoryObject(
				key		= Callback(GetDirectory, title=L('My Groups'), url=VIMEO_MY_GROUPS % user),
				title	= L('My Groups')
			),
			DirectoryObject(
				key		= Callback(GetVideos, title=L('Watch Later'), url=VIMEO_WATCH_LATER, cacheTime=300, ajaxRequest = True),
				title	= L('Watch Later')
			),
			DirectoryObject(
				key		= Callback(GetMySubscriptions, title=L('My Subscriptions')),
				title	= L('My Subscriptions')
			)
		]
	)

	return oc

####################################################################################################
def LoggedIn():

	html = HTML.ElementFromURL(VIMEO_URL, cacheTime=0)

	if len(html.xpath('//a[contains(@href, "/log_out")]')) > 0:
		Log(' --> User is logged in')
		return True

	return False

####################################################################################################
def Login():

	Log(' --> Trying to log in')
	html = HTTP.Request('https://vimeo.com/log_in', cacheTime=0).content
	token = RE_TOKEN.search(html).group('xsrft')

	post = {
		'action': 'login',
		'service': 'vimeo',
		'email': Prefs['email'],
		'password': Prefs['password'],
		'token': token
	}

	headers = {
		'Cookie': 'xsrft=%s' % token
	}

	login = HTTP.Request('https://vimeo.com/log_in', post, headers).content

####################################################################################################
def GetUsername():

	html = HTML.ElementFromURL(VIMEO_URL)
	username = html.xpath('//a[text()="Me"]')[0].get('href').split('/')[1]

	return username

####################################################################################################
def TimeToMs(timecode):

	seconds = 0
	duration = timecode.split(':')
	duration.reverse()

	for i in range(0, len(duration)):
		seconds += int(duration[i]) * (60**i)

	return seconds * 1000
