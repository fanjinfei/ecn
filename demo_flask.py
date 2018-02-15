# from http://flask.pocoo.org/ tutorial
from flask import Flask, request
from flask import render_template, redirect, g, url_for, abort
from flask import send_from_directory
from flask.ext.babel import Babel
from flask_paginate import Pagination, get_page_parameter
import urllib
import requests
import json
import sys

import pprint

templates_dir = sys.argv[1]
static_dir = sys.argv[2]
end_point = 'http://f7wcmstestb2.statcan.ca:9601'
base_url = 'http://dev-b-es-fusion01.stc.ca:8080/json/?'
app = Flask(__name__, template_folder=templates_dir)
app.config['BABEL_TRANSLATION_DIRECTORIES'] = './i18n'
babel = Babel(app)
'''
pybabel init -i fr.po -d ./i18n/ -l fr
pybabel compile -d i18n/
later only 	$ pybabel update -i fr.po -d i18n
'''

@app.before_request
def before():
    if request.view_args and 'lang_code' in request.view_args:
        if request.view_args['lang_code'] not in ('fr', 'en'):
            return abort(404)
        g.current_lang = request.view_args['lang_code']
        request.view_args.pop('lang_code')

@babel.localeselector
def get_locale():
    return g.get('current_lang', 'en')

@app.route('/')
def root():
    return redirect(url_for('ecn_search', lang_code='en'))

def _send_static(filename):
    return send_from_directory(static_dir, filename)

#@app.route('/<string:page_name>/')
@app.route('/static/<string:page_name>')
def static_page(page_name):
    return _send_static(page_name)
    #return render_template('%s' % page_name)

@app.route('/css/<string:page_name>')
def css_page(page_name):
    return _send_static(page_name)

@app.route('/images/wb-icon/<string:page_name>')
def images_page(page_name):
    print 'images', page_name
    return _send_static( 'images/wb-icon/'+page_name)

def _get_search(q, start_page=1, page_size=20, labels=None, burl=None, lang='en', sort=''):
    start = (start_page-1)*page_size
    if not burl: burl=base_url
    fields = ''
    if labels:
        #q = q + '+label%3A' +label
        for label in labels:
            fields += '&fields.label={0}'.format(label)
    url = ''.join([burl, 'q=', q, '&start={0}&num={1}&lang={2}&sort={3}'.format(start,page_size, lang, sort)]) + fields
    print (url)
    user_agent = {'User-agent': 'statcan search'}
    r = requests.get(url=url, headers=user_agent, timeout=10)
    if r.status_code == requests.codes.ok:
        return r.text
    else:
        return None

date_range = {
    "timestamp:[now-1d/d TO *]":[0,'past day'], 
    "timestamp:[now-7d/d TO *]":[1,'past week'],
    "timestamp:[now-30d/d TO *]":[2, 'past month'],
    "timestamp:[now-1y/d TO *]":[3, 'past year'],
    "timestamp:[* TO now-1y-1d/d]":[4, 'one year older'],
}
def _get_search_post(q, start_page=1, page_size=20, labels=None, burl=None, lang='en', sort='', ex_q=''):
    start = (start_page-1)*page_size
    if not burl: burl=base_url
    if burl[-1] == '?': burl = burl[:-1]

    payload= {'q':q,
              'start':start,
              'num':page_size,
              'lang':lang,
              'sort':sort,
              'facet.query':list(date_range.keys())
            }
    if labels:
        payload['fields.label'] = labels
    if ex_q:
        payload['ex_q'] = ex_q

    print (burl, payload)
    user_agent = {'User-agent': 'statcan search'}
    r = requests.post(url=burl, headers=user_agent, data=payload, timeout=10)
    if r.status_code == requests.codes.ok:
        print r.text[-200:]
        return r.text
    else:
        return None

@app.route("/suggest", methods=['GET'])
def suggest():
    qval = request.args.get('query')
    sub = request.args.get('sub')
    callback = request.args.get('callback')
    words = qval.split(' ')
    prefix = ' '.join(words[:-1])
    if not words[-1]:
        return '/**/'+callback+ '({"response": {"status": 0, "version": 11.4, "result": {"hits": [], "total": "0", "num": "0", "took": "0"}}})'
    url = end_point+u'/suggest?callback={1}&query={0}&fields=_default,content,title&num=20'.format(words[-1], callback)
    if sub:
        if sub =='daily':
            sub='daily_archive,daily'
        url += '&tags={0}'.format(sub)
    r = requests.get(url=url, timeout=2)
    print "TO FESS suggest",sub, url
    if r.status_code == requests.codes.ok:
        #return r.text
        startp = len(callback) +5
        rjhits= json.loads(r.text[startp:-1])
        res = rjhits['response']['result'].get('hits', [])
        for p in res:
            p['text'] = prefix + ' ' + p['text']
        rjhits['response']['result']['hits'] = res
        rtext = r.text[:startp] + json.dumps(rjhits) + ')'
        print rtext
        return rtext

@app.route("/<lang_code>/search", methods=['GET'])
def search():
    qval = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    print (qval, request.get_json(), request.data, request.args)
    res = None
    pagination = None
    if qval:
        res = _get_search(qval, page)
        if res:
            res = json.loads(res)['response']
            total, per_page = res['record_count'], 20
            href=''.join(['/en/search?q=',qval,
                           '&num=20&page={0}'])
            if total > per_page:
                pagination = Pagination(page=page, per_page=per_page,
                                    href = href, bs_version=4,
                                    total=total, record_name='users')
    return render_template('index.html', qval=qval or '', res=res, locale=get_locale(),
                           pagination=pagination)

@app.route("/<lang_code>/ib_search", methods=['GET'])
def ib_search():
    qval = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    print (qval, request.get_json(), request.data, request.args)
    res = None
    pagination = None
    if qval:
        res = _get_search(qval, page, 20, 'ib', 'http://f7wcmstestb2.statcan.ca:9601/json/?')
        if res:
            res = json.loads(res)['response']
            total, per_page = res['record_count'], 20
            href=''.join(['/en/ib_search?q=',qval,
                           '&num=20&page={0}'])
            if total > per_page:
                pagination = Pagination(page=page, per_page=per_page,
                                    href = href, bs_version=4,
                                    total=total, record_name='users')
    return render_template('index_ib.html', qval=qval or '', res=res, locale=get_locale(),
                           pagination=pagination)
def qfilter(val):
    r = []
    for c in val:
        if c.isalnum() or c in ['-', '\'', '"', '+', '*']:
            r.append(c)
        else:
            r.append(' ')
    return u''.join(r) 

@app.route("/<lang_code>/ecn_search", methods=['GET'])
def ecn_search():
    qval = request.args.get('q')
    sort = request.args.get('sort', '')
    ex_q = request.args.get('ex_q', '')
    print type(qval), qval
    page = request.args.get('page', 1, type=int)
    print (qval, request.get_json(), request.data, request.args)
    res = None
    pagination = None
    facet = {}
    
    sub = request.args.get('sub', '')
    if not sub or sub=='all':
        labels = ['ecn', 'human_resource', 'hub']
    elif sub =='daily':
        labels = ['daily_archive', 'daily', 'daily_latest']
    elif sub =='hr':
        labels = ['human_resource']
    elif sub in ['statcan', 'phone', 'hub']:
        labels = [sub]
    else:
        sub=''
        labels = ['ecn', 'human_resource', 'hub']
    urls = {}
    url_sbase = u'/{0}/ecn_search?q={1}&sort={2}'.format(get_locale(),qval or '', sort)
    urls['all'] = url_sbase + '&sub=all'
    urls['hub'] = url_sbase + '&sub=hub'
    urls['hr'] = url_sbase + '&sub=hr'
    urls['daily'] = url_sbase + '&sub=daily'
    urls['phone'] = url_sbase + '&sub=phone'
    urls['statcan'] = url_sbase + '&sub=statcan'
    lang = get_locale()
    def get_facet_query(res):
        if not res: return []
        data = []
        for item in res:
            val, count = item['value'], item['count']
            fa_label = date_range.get(val, 'unknown')
            data.append( [fa_label[0], fa_label[1], count, val])
        data.sort(key=lambda x:x[0])
        facet_burl = u'/{0}/ecn_search?q={1}&sort={2}&sub={3}&ex_q='.format(
                    get_locale(),qval or '', sort, sub)
        ndata = []
        for x in data:
            if x[3]== ex_q:
                ndata.append( [x[1], x[2], facet_burl, 1])
            else:
                ndata.append( [x[1], x[2], facet_burl+x[3], 0])
        return ndata
    if qval:
        #TODO: escape : -> \:
#        res = _get_search(qval.replace(' ', '+'), page, 20, labels,
#                          'http://f7wcmstestb2.statcan.ca:9601/json/?', lang)
        res = _get_search_post(qfilter(qval), page, 20, labels,
                          'http://f7wcmstestb2.statcan.ca:9601/json/?', lang, sort, ex_q)
        if res:
            res = json.loads(res)['response']
            facet = get_facet_query(res.get('facet_query', None))
            total, per_page = res.get('record_count', 0), 20
            total = min(total, 10000) # elastic search index.max_result_window [default] = 10000
            print 'total', total
            href=''.join(['/{0}/ecn_search?q='.format(get_locale()), urllib.quote(qval.encode('utf-8')),
                           '&sub={0}&sort={1}'.format(sub, sort),
                           '&num=20&page={0}'])
            print 'phref:', href
            for item in res.get('result', []):
                if item['content_description'].find('<strong>') == -1:
                    item['content_description'] = item['content_description'][:400]
            if total > per_page:
                pagination = Pagination(page=page, per_page=per_page,
                                    href = href, bs_version=4,
                                    total=total, record_name='users')
    return render_template('index_ecn.html', qval=qval or '', sub=sub, urls=urls, res=res, locale=get_locale(),
                           pagination=pagination, sort=sort, facet=facet, ex_q=ex_q)


@app.route("/<lang_code>/adv_search", methods=['GET'])
def advanced_search():
    qval=None
    res=None
    return render_template('adv.html', qval=qval or '', res=res, locale=get_locale(),
                           pagination=None)

@app.route('/favicon.ico')
def favicon():
    return redirect('/static/favicon.ico')

def test():
    r = json.loads(_get_search('price'))
    pprint.pprint(r)

if __name__ == "__main__":
    #print app.url_map
    app.run(host='0.0.0.0', port=8000)
    #test()

