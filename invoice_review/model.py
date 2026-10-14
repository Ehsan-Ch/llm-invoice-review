import json
import time
import urllib.request
from urllib.parse import urlsplit
from .core import SCHEMA,PROMPT

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('Redirects are disabled.')

class LocalModel:
    def __init__(self,endpoint='http://127.0.0.1:8095',model='invoice-qwen'):
        u=urlsplit(endpoint)
        if u.scheme!='http' or u.hostname not in ('localhost','127.0.0.1','::1') or not u.port or u.path not in ('','/') or u.query or u.fragment or u.username or u.password:
            raise ValueError('Use a loopback HTTP origin with an explicit port.')
        self.endpoint=endpoint.rstrip('/');self.model=model
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def complete(self,text):
        data={'model':self.model,'messages':[{'role':'system','content':PROMPT},{'role':'user','content':json.dumps({'invoice_text':text})}],
              'temperature':0,'seed':41,'max_tokens':900,'stream':False,'chat_template_kwargs':{'enable_thinking':False},
              'response_format':{'type':'json_object','schema':SCHEMA}}
        request=urllib.request.Request(self.endpoint+'/v1/chat/completions',data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
        start=time.perf_counter()
        with self.opener.open(request,timeout=120) as response:body=response.read(1000001)
        if len(body)>1000000:raise ValueError('Oversized model response.')
        obj=json.loads(body);choice=obj['choices'][0]
        return {'content':choice['message']['content'],'finish_reason':choice.get('finish_reason'),
                'usage':obj.get('usage',{}),'latency_seconds':round(time.perf_counter()-start,3)}
