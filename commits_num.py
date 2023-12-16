import requests
import re

# from https://gist.github.com/codsane/25f0fd100b565b3fce03d4bbd7e7bf33

def commitCount(u, r):
	# print('https://api.github.com/repos/{}/{}/commits?per_page=1'.format(u, r))
    try:
        res = requests.get('https://api.github.com/repos/{}/{}/commits?per_page=1'.format(u, r))
        # return res
        if hasattr(res, 'links'):
            return re.search('\d+$', res.links['last']['url']).group()
        return '0'
    except:
        return '0'
#
def latestCommitInfo(u, r):
	""" Get info about the latest commit of a GitHub repo """
	response = requests.get('https://api.github.com/repos/{}/{}/commits?per_page=1'.format(u, r))
	commit = response.json()[0]; commit['number'] = re.search('\d+$', response.links['last']['url']).group()
	return commit


    
# u='easyw'
# r='kicadStepUpMod'
# print(int(commitCount(u, r)))
# # print(latestCommitInfo(u, r))
# 
# u='easyw'
# r='Manipulator'
# print(int(commitCount(u, r)))