"""Loopback HTTP, subprocess and installer tests; no paid or external API calls."""
from __future__ import annotations
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SKILL=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SKILL/'scripts'))
from munjanglib.common import ContractError, dumps, loads, read_text
from munjanglib.engine import Session, run_session
from munjanglib.providers import checked_base_url, HTTPProvider, CommandProvider, DemoProvider, Router
SOURCE='연구팀은 분석을 진행했다. 참가자는 12명이다.\n'
FINAL='연구팀은 분석했다. 참가자는 12명이다.\n'


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.seen.append((self.path,payload,dict(self.headers)))
        if self.server.mode=='redirect':
            self.send_response(302);self.send_header('Location','/other');self.end_headers();return
        if self.server.mode=='error':
            self.send_response(429);self.end_headers();self.wfile.write(b'SECRET_ERROR_BODY');return
        is_resp=self.path.endswith('/responses')
        data=json.loads(payload['input'] if is_resp else payload['messages'][1]['content'])
        if 'candidate_text' in data:stage='verify'
        elif 'diagnosis' in data:stage='revise'
        elif data['brief']['mode']=='draft' and not data['current_text']:stage='draft'
        else:stage='diagnose'
        answer=dumps(DemoProvider().complete({'stage':stage,'data':data}))
        if self.server.mode=='malformed_model':answer='```json\n{}\n```'
        if is_resp:
            obj={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':answer}]}]}
            if self.server.mode=='incomplete':obj['status']='incomplete'
            if self.server.mode=='refusal':obj['output'][0]['content']=[{'type':'refusal','refusal':'No.'}]
        else:
            obj={'choices':[{'finish_reason':'stop','message':{'content':answer}}]}
            if self.server.mode=='incomplete':obj['choices'][0]['finish_reason']='length'
            if self.server.mode=='refusal':obj['choices'][0]['message']['refusal']='No.'
            if self.server.mode=='tools':obj['choices'][0]['finish_reason']='tool_calls'
        body=dumps(obj).encode() if self.server.mode!='malformed_http' else b'<html>Error</html>'
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)


@contextmanager
def server(mode='ok'):
    s=ThreadingHTTPServer(('127.0.0.1',0),Handler);s.mode=mode;s.seen=[]
    thread=threading.Thread(target=lambda:s.serve_forever(poll_interval=.01),daemon=True);thread.start()
    try:yield s,f'http://127.0.0.1:{s.server_address[1]}/v1'
    finally:s.shutdown();s.server_close();thread.join(timeout=2)


class URLTests(unittest.TestCase):
    def test_loopback_http(self):self.assertEqual(checked_base_url('http://127.0.0.1:1234/v1/',False),'http://127.0.0.1:1234/v1')
    def test_ipv6_loopback(self):self.assertEqual(checked_base_url('http://[::1]/v1',False),'http://[::1]/v1')
    def test_localhost(self):self.assertTrue(checked_base_url('http://localhost/v1',False))
    def test_remote_needs_optin(self):
        with self.assertRaises(ContractError):checked_base_url('https://api.example.org/v1',False)
    def test_remote_https_allowed_explicitly(self):self.assertTrue(checked_base_url('https://api.example.org/v1',True))
    def test_remote_http_refused_even_optin(self):
        with self.assertRaises(ContractError):checked_base_url('http://api.example.org/v1',True)
    def test_embedded_credentials_refused(self):
        with self.assertRaises(ContractError):checked_base_url('https://user:key@api.example.org/v1',True)
    def test_query_refused(self):
        with self.assertRaises(ContractError):checked_base_url('https://api.example.org/v1?key=secret',True)
    def test_fragment_refused(self):
        with self.assertRaises(ContractError):checked_base_url('https://api.example.org/v1#x',True)
    def test_file_scheme_refused(self):
        with self.assertRaises(ContractError):checked_base_url('file:///etc/passwd',True)
    def test_deceptive_localhost_refused(self):
        with self.assertRaises(ContractError):checked_base_url('http://localhost.example.org/v1',False)


class HTTPTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
    def tearDown(self):self.tmp.cleanup()
    def request(self):return Session.create(self.root/'request',SOURCE,{}).request()
    def test_responses_loop_end_to_end(self):
        with server() as (s,url):
            p=HTTPProvider(url,'fixture',key_env='');session=Session.create(self.root/'run',SOURCE,{},p.label)
            r=run_session(session,p);self.assertEqual(read_text(session.directory/'final.txt'),FINAL)
            self.assertEqual(len(s.seen),4);self.assertEqual(r['accepted_rounds'],1)
            self.assertFalse(s.seen[0][1]['store']);self.assertIn('instructions',s.seen[0][1])
            self.assertEqual(r['external_fact_check'],'not_performed_by_runtime')
    def test_chat_loop_end_to_end(self):
        with server() as (s,url):
            p=HTTPProvider(url,'fixture',kind='chat-completions',key_env='');session=Session.create(self.root/'run',SOURCE,{},p.label)
            run_session(session,p);self.assertEqual(read_text(session.directory/'final.txt'),FINAL)
            self.assertEqual(len(s.seen),4);self.assertFalse(s.seen[0][1]['stream'])
    def test_json_mode_responses(self):
        with server() as (s,url):
            HTTPProvider(url,'fixture',key_env='',json_mode=True).complete(self.request())
            self.assertEqual(s.seen[0][1]['text']['format']['type'],'json_object')
    def test_legacy_token_parameter_chat(self):
        with server() as (s,url):
            HTTPProvider(url,'fixture',kind='chat-completions',key_env='',token_parameter='max_tokens',json_mode=True).complete(self.request())
            self.assertIn('max_tokens',s.seen[0][1]);self.assertNotIn('max_completion_tokens',s.seen[0][1])
            self.assertEqual(s.seen[0][1]['response_format']['type'],'json_object')
    def test_key_only_from_selected_environment(self):
        with server() as (s,url),patch.dict(os.environ,{'MUNJANG_FIXTURE_KEY':'test-not-a-real-secret'}):
            HTTPProvider(url,'fixture',key_env='MUNJANG_FIXTURE_KEY').complete(self.request())
            self.assertEqual(s.seen[0][2]['Authorization'],'Bearer test-not-a-real-secret')
            self.assertNotIn('test-not-a-real-secret',dumps(s.seen[0][1]))
    def test_http_error_not_retried_and_body_not_echoed(self):
        with server('error') as (s,url):
            with self.assertRaises(ContractError) as e:HTTPProvider(url,'fixture',key_env='').complete(self.request())
            self.assertEqual(len(s.seen),1);self.assertNotIn('SECRET_ERROR_BODY',str(e.exception))
    def test_redirect_not_followed(self):
        with server('redirect') as (s,url):
            with self.assertRaises(ContractError):HTTPProvider(url,'fixture',key_env='').complete(self.request())
            self.assertEqual(len(s.seen),1)
    def test_incomplete_responses(self):
        with server('incomplete') as (s,url):
            with self.assertRaises(ContractError):HTTPProvider(url,'fixture',key_env='').complete(self.request())
    def test_incomplete_chat(self):
        with server('incomplete') as (s,url):
            with self.assertRaises(ContractError):HTTPProvider(url,'fixture',kind='chat-completions',key_env='').complete(self.request())
    def test_refusal_responses(self):
        with server('refusal') as (s,url):
            with self.assertRaises(ContractError):HTTPProvider(url,'fixture',key_env='').complete(self.request())
    def test_refusal_chat(self):
        with server('refusal') as (s,url):
            with self.assertRaises(ContractError):HTTPProvider(url,'fixture',kind='chat-completions',key_env='').complete(self.request())
    def test_tools_not_executed(self):
        with server('tools') as (s,url):
            with self.assertRaises(ContractError):HTTPProvider(url,'fixture',kind='chat-completions',key_env='').complete(self.request())
    def test_malformed_outer_json(self):
        with server('malformed_http') as (s,url):
            with self.assertRaises(ContractError):HTTPProvider(url,'fixture',key_env='').complete(self.request())
    def test_malformed_model_json(self):
        with server('malformed_model') as (s,url):
            with self.assertRaises(ContractError):HTTPProvider(url,'fixture',key_env='').complete(self.request())
    def test_endpoint_is_in_provenance(self):
        a=HTTPProvider('http://127.0.0.1:8000/v1','fixture',key_env='')
        b=HTTPProvider('http://127.0.0.1:9000/v1','fixture',key_env='')
        self.assertNotEqual(a.label,b.label)
    def test_routing_selects_only_verifier(self):
        class P:
            def __init__(self,label):self.label=label;self.calls=[]
            def complete(self,q):self.calls.append(q['stage']);return {}
        a,b=P('writer'),P('reviewer');r=Router(a,b)
        for stage in ['draft','diagnose','revise','verify']:r.complete({'stage':stage})
        self.assertEqual(a.calls,['draft','diagnose','revise']);self.assertEqual(b.calls,['verify'])


class CommandTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
    def tearDown(self):self.tmp.cleanup()
    def test_json_stdin_stdout(self):
        p=CommandProvider([sys.executable,'-c','import json,sys; q=json.load(sys.stdin); print(json.dumps({"stage":q["stage"]}))'])
        self.assertEqual(p.complete({'stage':'diagnose'}),{'stage':'diagnose'})
    def test_shell_metacharacters_are_literal(self):
        arg='a; echo SHOULD_NOT_RUN && x'
        p=CommandProvider([sys.executable,'-c','import json,sys; print(json.dumps({"value":sys.argv[1]}))',arg])
        self.assertEqual(p.complete({})['value'],arg)
    def test_nonzero_exit(self):
        p=CommandProvider([sys.executable,'-c','import sys; sys.stderr.write("SECRET"); sys.exit(3)'])
        with self.assertRaises(ContractError) as e:p.complete({})
        self.assertNotIn('SECRET',str(e.exception))
    def test_malformed_output(self):
        p=CommandProvider([sys.executable,'-c','print("not JSON")'])
        with self.assertRaises(ContractError):p.complete({})
    def test_timeout(self):
        p=CommandProvider([sys.executable,'-c','import time;time.sleep(1)'],timeout=.02)
        with self.assertRaises(ContractError):p.complete({})
    def test_adapter_identity_changes_with_argv(self):
        a=CommandProvider([sys.executable,'one.py']);b=CommandProvider([sys.executable,'two.py'])
        self.assertNotEqual(a.label,b.label)
    def test_empty_argv(self):
        with self.assertRaises(ContractError):CommandProvider([])
    def test_command_full_loop(self):
        script=self.root/'adapter with 한글.py'
        script.write_text('import json,sys\nsys.path.insert(0,'+repr(str(SKILL/'scripts'))+')\nfrom munjanglib.providers import DemoProvider\nsys.stdout.reconfigure(encoding="utf-8")\nq=json.loads(sys.stdin.buffer.read().decode("utf-8"))\nprint(json.dumps(DemoProvider().complete(q),ensure_ascii=False))\n',encoding='utf-8')
        p=CommandProvider([sys.executable,str(script)]);session=Session.create(self.root/'run',SOURCE,{},p.label)
        r=run_session(session,p);self.assertEqual(r['accepted_rounds'],1);self.assertEqual(session.current,FINAL)


ROOT=SKILL.parents[1]
HAS_INSTALLER=(ROOT/'tools/install.py').is_file()
if HAS_INSTALLER:
    spec=importlib.util.spec_from_file_location('munjang_installer',ROOT/'tools/install.py')
    installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)


@unittest.skipUnless(HAS_INSTALLER,'Standalone skill excludes plugin-level installer')
class InstallerTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
    def tearDown(self):self.tmp.cleanup()
    def jobs(self,**kw):return installer.plan('codex','project',self.root/'프로젝트 with spaces',**kw)
    def test_dry_run_does_not_write(self):
        j=self.jobs();r=installer.install(j,dry_run=True)
        self.assertEqual(r[0]['action'],'would_install');self.assertFalse(j[0][1].exists())
    def test_codex_install_and_run(self):
        j=self.jobs();installer.install(j);target=j[0][1]
        self.assertTrue((target/'SKILL.md').is_file())
        self.assertFalse(list(target.rglob('*.pyc')))
        r=subprocess.run([sys.executable,str(target/'scripts/workbench.py'),'--version'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0);self.assertEqual(r.stdout.strip(),'1.0.0')
    def test_existing_not_overwritten(self):
        j=self.jobs();installer.install(j)
        with self.assertRaises(ValueError):installer.install(j)
    def test_force_keeps_backup(self):
        j=self.jobs();installer.install(j);(j[0][1]/'private-note.txt').write_text('keep')
        r=installer.install(j,force=True);backup=Path(r[0]['backup'])
        self.assertEqual((backup/'private-note.txt').read_text(),'keep');self.assertFalse((j[0][1]/'private-note.txt').exists())
    def test_agents_installed(self):
        j=self.jobs(with_agents=True);installer.install(j)
        self.assertEqual(len(j),4);self.assertTrue(all(dst.exists() for _,dst in j))
    def test_claude_agent_install(self):
        j=installer.plan('claude','project',self.root,with_agents=True);installer.install(j)
        self.assertTrue((self.root/'.claude/skills/korean-writing/SKILL.md').exists())
        self.assertEqual(len(list((self.root/'.claude/agents').glob('*.md'))),3)
    def test_generic_destination(self):
        target=self.root/'custom/korean-writing';j=installer.plan('generic','user',destination=target);installer.install(j)
        self.assertTrue((target/'SKILL.md').exists())
    def test_generic_requires_destination(self):
        with self.assertRaises(ValueError):installer.plan('generic','user')
    def test_wrong_skill_directory_name(self):
        with self.assertRaises(ValueError):installer.plan('generic','user',destination=self.root/'bad')
    def test_preflight_blocks_partial_on_conflict(self):
        j=self.jobs(with_agents=True);j[-1][1].parent.mkdir(parents=True);j[-1][1].write_text('existing')
        with self.assertRaises(ValueError):installer.install(j)
        self.assertFalse(j[0][1].exists())
    def test_symlink_target_refused(self):
        real=self.root/'real';real.mkdir();link=self.root/'link'
        try:link.symlink_to(real,target_is_directory=True)
        except OSError:self.skipTest('Symlinks not available in this environment')
        j=installer.plan('generic','user',destination=link/'korean-writing')
        with self.assertRaises(ValueError):installer.install(j)


if __name__=='__main__':unittest.main()
