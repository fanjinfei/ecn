# from http://flask.pocoo.org/ tutorial
from flask import Flask, request
from flask import render_template, redirect, g, url_for, abort
from flask import send_from_directory
from flask.ext.babel import Babel
from flask_paginate import Pagination, get_page_parameter
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

def _get_search(q, start_page=1, page_size=20, labels=None, burl=None):
    start = (start_page-1)*page_size
    if not burl: burl=base_url
    fields = ''
    if labels:
        #q = q + '+label%3A' +label
        for label in labels:
            fields += '&fields.label={0}'.format(label)
    url = ''.join([burl, 'q=', q, '&start={0}&num={1}'.format(start,page_size)]) + fields
    print (url)
    user_agent = {'User-agent': 'statcan search'}
    r = requests.get(url=url, headers=user_agent, timeout=10)
    if r.status_code == requests.codes.ok:
        return r.text
    else:
        return None

@app.route("/suggest", methods=['GET'])
def suggest():
    qval = request.args.get('query')
    callback = request.args.get('callback')
    words = qval.split(' ')
    prefix = ' '.join(words[:-1])
    if not words[-1]:
        return '/**/'+callback+ '({"response": {"status": 0, "version": 11.4, "result": {"hits": [], "total": "0", "num": "0", "took": "0"}}})'
    url = end_point+'/suggest?callback={1}&query={0}&fields=_default,content,title&num=20'.format(words[-1], callback)
    r = requests.get(url=url, timeout=2)
    if r.status_code == requests.codes.ok:
        #return r.text
        startp = len(callback) +5
        rjhits= json.loads(r.text[startp:-1])
        res = rjhits['response']['result']['hits']
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

@app.route("/<lang_code>/ecn_search", methods=['GET'])
def ecn_search():
    qval = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    print (qval, request.get_json(), request.data, request.args)
    res = None
    pagination = None
    
    sub = request.args.get('sub', '')
    if not sub:
        labels = ['ecn', 'phone']
    else:
        labels = [sub]
    urls = {}
    urls['all'] = '/{0}/ecn_search?q={1}'.format(get_locale(),qval)
    urls['phone'] = urls['all']+ '&sub=phone'
    urls['statcan'] = urls['all']+ '&sub=statcan'
    if qval:
        #TODO: escape : -> \:
        res = _get_search(qval.replace(' ', '+'), page, 20, labels, 'http://f7wcmstestb2.statcan.ca:9601/json/?')
        if res:
            res = json.loads(res)['response']
            total, per_page = res.get('record_count', 0), 20
            href=''.join(['/{0}/ecn_search?q='.format(get_locale()),qval, '&sub={0}'.format(sub),
                           '&num=20&page={0}'])
            for item in res.get('result', []):
                if item['content_description'].find('<strong>') == -1:
                    item['content_description'] = item['content_description'][:400]
            if total > per_page:
                pagination = Pagination(page=page, per_page=per_page,
                                    href = href, bs_version=4,
                                    total=total, record_name='users')
    return render_template('index_ecn.html', qval=qval or '', sub=sub, urls=urls, res=res, locale=get_locale(),
                           pagination=pagination)


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

