"""Optional zero-API-fee, local-only LLM ideation. No tools or execution rights."""
import json
import urllib.error
import urllib.request

HOST = 'http://127.0.0.1:11434'

def brainstorm(subject: str, model: str='gemma3:1b'):
    if not subject or len(subject)>150:
        raise ValueError('Subject must be 1 to 150 characters')
    if not model or len(model)>120 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:._-/' for c in model):
        raise ValueError('Invalid local model name')
    instruction=('Generate three novel, useful, zero-upfront-cost DIGITAL PRODUCT draft ideas for: '+subject+'\n'
                 'Return a numbered list, each with customer problem, original deliverable and a no-spend validation test. '
                 'Never promise income, pretend market research, use protected marks, scrape accounts, or propose paid actions. '
                 'Suggestions are NOT approved to publish or spend. No hidden platform tools.')
    body=json.dumps({'model':model,'prompt':instruction,'stream':False,
                     'think':False if model.startswith('qwen3:') else None,'options':{'temperature':0.5,'num_predict':180}}).encode()
    request=urllib.request.Request(HOST+'/api/generate',data=body,
             headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(request,timeout=300) as result:
        data=json.loads(result.read(120000))
    return data.get('response','(model returned no draft)')
