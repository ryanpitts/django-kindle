from django.conf import settings
from django.http import Http404
from django.views.generic import simple, list_detail
from django.contrib.sites.models import Site

import datetime
import time
from dateutil.relativedelta import *

from cannonball.stories.models import Story, BaseSection

# change this value to govern traversal of your archives
allowed_timeframe = datetime.datetime.today()+relativedelta(days=-6)


def kindle_article_detail(request, object_id):
    '''
    View returning an individual print-edition story for Kindle ingestion.
    
    Story.live_objects goes through a manager on our Story model, filtering the queryset
    for is_live=True, pubdate__lte=now, sites=settings.SITE_ID. The Story model also has
    fields to hold additional information from our print publication, so by making sure
    those contain data, we filter for ONLY stories from the print edition.
    
    This feeds an NITF template, which naturally calls fields specific to our particular
    Story model. Easy enough to tweak, though.
    
    NOTE: Our Story model has an m2m relationship with our Photo model, so associated
    images are pulled into the template that way. If you handle story photos some other
    way, you'll probably want to use this view to pass them into context.
    
    '''
    qs = Story.live_objects.filter(pubdate__gte=allowed_timeframe).exclude(print_sectionletter=None).exclude(print_pagenumber=None)
    return list_detail.object_detail(
        request,
        queryset = qs,
        object_id = object_id,
        template_object_name = "article",
        template_name = "kindle/kindle_article_file.xml",
    )


def kindle_article_manifest(request, year, month, day, section, template='kindle/kindle_article_manifest.xml'):
    '''
    View returning a list of print-edition stories within a section for a given pubdate.
    
    BaseSection is the website model that (basically) maps to print edition sections.
    So we have BaseSections for News, Sports, Opinion, etc. On the website, BaseSections
    collect their stories based on Categories (because a BaseSection may contain more
    than one Category of Story). Hence the generation of cat_list for the queryset filter.
    
    The section_manifest template (see kindle_section_manifest below) hardcodes a "Front Page"
    section, because Kindle wants to provide a specific list of front-page stories. We don't have
    a BaseSection like that, so we fake it here by filtering for stories that appeared on A1.
    
    This feeds an RSS 2.0 template.
    
    '''
    SITE = Site.objects.get_current()
    try:
        year = "%04d" % int(year)
        month = "%02d" % int(month)
        day = "%02d" % int(day)
        search_date = datetime.datetime(*time.strptime(year+month+day, '%Y'+'%m'+'%d')[:3])
        year = int(year)
        month = int(month)
        day = int(day)
    except ValueError:
        raise Http404
        
    if allowed_timeframe and search_date < allowed_timeframe:
        raise Http404
        
    is_frontpage = False
    if section == 'front-page':
        stories = Story.live_objects.filter(pubdate__year=year, pubdate__month=month, pubdate__day=day).filter(print_sectionletter__exact = 'A').filter(print_pagenumber__exact='1')
        is_frontpage = True
    else:
        section = BaseSection.objects.get(slug__exact=section)
        cat_list = section.categories.all()
        stories = Story.live_objects.filter(pubdate__year=year, pubdate__month=month, pubdate__day=day).exclude(print_sectionletter=None).exclude(print_pagenumber=None).exclude(print_sectionletter__exact='A',print_pagenumber__exact='1').filter(categories__in=cat_list).order_by('print_sectionletter', 'print_pagenumber').distinct()
        
    return simple.direct_to_template(
        request,
        template = template,
        extra_context = {
            'article_list': stories,
            'pubdate': search_date,
            'section': section,
            'is_frontpage': is_frontpage,
            'site': SITE,
        }
    )


def kindle_section_manifest(request, year=None, month=None, day=None, template='kindle/kindle_section_manifest.xml'):
    '''
    View returning a list of sections that contain stories for a given pubdate. Default is today's date,
    but access to back pubdates is available based on allowed_timeframe.
    
    See kindle_article_manifest above for information about BaseSection. For the Kindle edition
    of a newspaper, Amazon divides stories up into the same sections as the print edition. They want
    to present sections in a standard order for each edition, so first we find all the BaseSections
    for the site, then we test each to see whether they contain any stories for the pubdate. (There's
    probably a more graceful way to do this.)
    
    Once we have the list of all BaseSections that contain stories for the pubdate, we loop through
    and standardize the order.
    
    This feeds an RSS 2.0 template.
    
    '''
    SITE = Site.objects.get_current()
    sections = BaseSection.objects.filter(site__id__exact=settings.SITE_ID).filter(is_live__exact=True)
    #get me a date!
    if year == month == day == None:
        search_date = datetime.datetime.today().replace(hour=0,minute=0,second=0)
    else:
        try:
            search_date = datetime.datetime(*time.strptime(year+month+day, '%Y'+'%m'+'%d')[:3])
        except ValueError:
            raise Http404
    
    if search_date:
        if allowed_timeframe and search_date < allowed_timeframe:
            raise Http404
        else:
            year = int(search_date.strftime('%Y')) 
            month = int(search_date.strftime('%m')) 
            day = int(search_date.strftime('%d'))
    
    #figure out sections for which we have stories for this pubdate
    sections_withstories = []
    for section in sections:
        cat_list = section.categories.all()
        stories = Story.live_objects.filter(pubdate__year=year, pubdate__month=month, pubdate__day=day).exclude(print_sectionletter=None).exclude(print_pagenumber=None).filter(categories__in=cat_list)
        if stories:
            sections_withstories.append(section)

    #now that we know which sections have stories, put them in the right order for Amazon
    section_list = []
    amazon_order = ['News','Sports','Business','Features','Idaho','Opinion','Nation/World']
    for a in amazon_order:
        for s in sections_withstories:
            if s.name == a:
                sections_withstories.remove(s)
                section_list.append(s)
    
    #append any leftover sections (i.e. things that run on specific days, like Outdoors, Food, Handle Extra)
    for s in sections_withstories:
        section_list.append(s)
    
    return simple.direct_to_template(
        request,
        template = template,
        extra_context = {
            'section_list': section_list,
            'pubdate': search_date,
            'site': SITE,
        }
    )
