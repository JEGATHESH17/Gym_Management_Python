import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from gym.db import gym

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body):
        data = json.dumps(body, default=str).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        key = os.environ['GYM_API_KEY']
        if not hmac.compare_digest(self.headers.get('Authorization',''), 'Bearer '+key):
            return self.reply(401, {'error':'Unauthorized'})
        name = self.path.removeprefix('/tools/')
        if not self.path.startswith('/tools/') or name not in TOOLS:
            return self.reply(404, {'error':'Unknown tool'})
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 16384:
                return self.reply(413, {'error':'Use a JSON body of at most 16 KiB'})
            args = json.loads(self.rfile.read(length))
            if not isinstance(args, dict):
                raise ValueError('JSON body must be an object')
            result = getattr(gym,name)(**args)
            self.reply(200, {'result':result})
        except (ValueError, TypeError) as exc:
            self.reply(400, {'error':str(exc)})
        except Exception:
            self.reply(500, {'error':'Database operation failed; check server setup and duplicate values.'})

TOOLS = {'add_member','search_members','create_plan','list_plans','activate_membership','record_payment','memberships','expiring_memberships'}
if __name__ == '__main__':
    if len(os.environ.get('GYM_API_KEY','')) < 32:
        raise SystemExit('Set GYM_API_KEY to a random value of at least 32 characters in .env')
    ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
