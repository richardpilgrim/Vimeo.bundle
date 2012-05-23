VIMEO_NAMESPACE = {'atom':'http://www.w3.org/2005/Atom', 'media':'http://search.yahoo.com/mrss/'}

VIMEO_URL = 'http://vimeo.com'
VIMEO_SEARCH = '%s/search/sort:relevant/format:detail?q=%%s' % VIMEO_URL
VIMEO_CATEGORIES = '%s/categories' % VIMEO_URL

VIMEO_FEATURED_CHANNELS = '%s/channels/page:%%d/sort:subscribers' % VIMEO_URL

VIMEO_CATEGORY_CHANNELS = '%s/categories/%%s/channels/page:%%d/sort:subscribers/format:detail' % VIMEO_URL
VIMEO_CATEGORY_GROUPS = '%s/categories/%%s/groups/page:%%d/sort:members/format:detail' % VIMEO_URL

VIMEO_CHANNEL = '%s/channels/%%s/videos/page:%%d/sort:preset/format:detail' % VIMEO_URL
VIMEO_GROUP = '%s/groups/%%s/videos/page:%%d/sort:date/format:detail' % VIMEO_URL

ICON = 'icon-default.png'
ART = 'art-default.jpg'

RE_MEDIA_CATEGORY = Regex('<media:category.+?<\/media:category>')
RE_CONTROL_CHARS = Regex(u'[\u0000-\u001F]')
RE_SUMMARY = Regex('(<p class="first">.*</p>)', Regex.DOTALL)

####################################################################################################
def Start():

	Plugin.AddPrefixHandler('/video/vimeo', MainMenu, 'Vimeo', ICON, ART)
	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')

	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = 'Vimeo'
	DirectoryObject.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:12.0) Gecko/20100101 Firefox/12.0'

####################################################################################################
def MainMenu():

	oc = ObjectContainer(
		objects = [
#			DirectoryObject(
#				key		= Callback(GetMyStuff),
#				title	= L('My Stuff')
#			),
			DirectoryObject(
				key		= Callback(GetVideos, title=L('Staff Picks'), directory_type='channels', id='staffpicks'),
				title	= L('Staff Picks')
			),
			DirectoryObject(
				key		= Callback(GetVideos, title=L('HD'), directory_type='channels', id='hd'),
				title	= L('HD')
			),
			DirectoryObject(
				key		= Callback(GetDirectory, title=L('Featured Channels'), directory_type='featured_channels'),
				title	= L('Featured Channels')
			),
			DirectoryObject(
				key		= Callback(Categories, title=L('Channels'), directory_type='channels'),
				title	= L('Channels')
			),
			DirectoryObject(
				key		= Callback(Categories, title=L('Groups'), directory_type='groups'),
				title	= L('Groups')
			),
#			InputDirectoryObject(
#				key		= Callback(Search),
#				title	= L('Search'),
#				prompt	= L('Search for Videos'),
#				thumb	= S('search.png')
#			),
			PrefsObject(
				title	= L('Preferences...'),
				thumb	= R('prefs.png')
			)
		]
	)

	return oc

####################################################################################################
def Categories(title, directory_type):

	oc = ObjectContainer(title2=title, view_group='List')

	for category in HTML.ElementFromURL(VIMEO_CATEGORIES).xpath('//ul[@id="categories"]/li/a'):
		title = category.xpath('./h2/text()')[0]
		category_id = category.get('href').rsplit('/',1)[1]

		oc.add(DirectoryObject(
			key = Callback(GetDirectory, title=title, directory_type=directory_type, category_id=category_id),
			title = title
		))

	return oc

####################################################################################################
def GetDirectory(title, directory_type=None, category_id=None, page=1):

	oc = ObjectContainer(title2=title, view_group='InfoList')

	if directory_type == 'channels':
		url = VIMEO_CATEGORY_CHANNELS % (category_id, page)
		type = directory_type
	elif directory_type == 'groups':
		url = VIMEO_CATEGORY_GROUPS % (category_id, page)
		type = directory_type
	elif directory_type == 'featured_channels':
		url = VIMEO_FEATURED_CHANNELS % page
		type = 'channels'

	html = HTML.ElementFromURL(url)

	for el in html.xpath('//ol[@id="browse_list"]/li'):
		id = el.xpath('.//a')[0].get('href').rsplit('/',1)[1]
		el_title = ''.join(el.xpath('.//p[@class="title"]//text()')).strip()
		try: summary = el.xpath('.//p[@class="description"]/text()')[0].strip()
		except: summary = ''
		thumb = el.xpath('.//img')[0].get('src')

		oc.add(DirectoryObject(
			key = Callback(GetVideos, title=el_title, directory_type=type, id=id),
			title = el_title,
			summary = summary,
			thumb = Resource.ContentsOfURLWithFallback(thumb, fallback='icon-default.png')
		))

	if len(html.xpath('//a[@rel="next"]')) > 0:
		oc.add(DirectoryObject(
			key = Callback(GetDirectory, title=title, directory_type=directory_type, category_id=category_id, page=page+1),
			title = L('More ...')
		))

	return oc

####################################################################################################
def GetVideos(title, directory_type=None, id=None, page=1):

	oc = ObjectContainer(title2=title, view_group='InfoList')

	if directory_type == 'channels':
		url = VIMEO_CHANNEL % (id, page)
	elif directory_type == 'groups':
		url = VIMEO_GROUP % (id, page)

	html = HTML.ElementFromURL(url)

	for el in html.xpath('//ol[@id="browse_list"]/li'):
		video_id = el.xpath('.//a')[0].get('href').rsplit('/',1)[1]
		el_title = el.xpath('.//p[@class="title"]/a/text()')[0].strip()
		summary = el.xpath('.//p[@class="description"]/text()')[0].strip()
		duration = TimeToMs(el.xpath('.//div[@class="duration"]/text()')[0])
		thumb = el.xpath('.//img')[0].get('src')

		oc.add(VideoClipObject(
			url = '%s/%s' % (VIMEO_URL, video_id),
			title = el_title,
			summary = summary,
			duration = duration,
			thumb = Resource.ContentsOfURLWithFallback(thumb, fallback='icon-default.png')
		))

	if len(html.xpath('//a[@rel="next"]')) > 0:
		oc.add(DirectoryObject(
			key = Callback(GetVideos, title=title, directory_type=directory_type, id=id, page=page+1),
			title = L('More ...')
		))

	return oc

####################################################################################################
def GetVideosRSS(url, title2):

	oc = ObjectContainer(title2=title2, view_group='InfoList')

	if url.find(VIMEO_URL) == -1:
		url = VIMEO_URL + url

	# Deal with non utf-8 character problem by removing the <media:category> element before parsing the document as XML
	xml = HTTP.Request(url).content
	xml = RE_MEDIA_CATEGORY.sub('', xml)

	# Remove any control characters, yucky fix :|
	# http://stackoverflow.com/questions/3748855/how-do-i-specify-a-range-of-unicode-characters-in-a-regular-expression-in-python
	# http://www.unicode.org/charts/PDF/U0000.pdf
	xml = RE_CONTROL_CHARS.sub('', xml)

	results = {}

	@parallelize
	def GetVideos():
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
					url = 'http://vimeo.com/%s' % key

					if 'video' in JSON.ObjectFromURL('http://player.vimeo.com/config/%s' % key, cacheTime=CACHE_1WEEK):
						results[num] = VideoClipObject(
							title = title,
							summary = summary,
							thumb = Resource.ContentsOfURLWithFallback(thumb, fallback='icon-default.png'),
							originally_available_at = date,
							url = url
						)
					else:
						Log('Video is private: %s - http://vimeo.com/%s' % (title, key))

				except:
					Log('Failed to load video: %s' % title)
					pass

	keys = results.keys()
	keys.sort()

	for key in keys:
		oc.add(results[key])

	return oc

####################################################################################################
def TimeToMs(timecode):

	seconds = 0
	duration = timecode.split(':')
	duration.reverse()

	for i in range(0, len(duration)):
		seconds += int(duration[i]) * (60**i)

	return seconds * 1000
