import re

# from https://gist.github.com/codsane/25f0fd100b565b3fce03d4bbd7e7bf33

def commitCount(u, r):
	# print('https://api.github.com/repos/{}/{}/commits?per_page=1'.format(u, r))
    try:
        #cuc
        import requests
        res = requests.get('https://api.github.com/repos/{}/{}/commits?per_page=1'.format(u, r))
        # return res
        if hasattr(res, 'links'):
            return re.search('\d+$', res.links['last']['url']).group()
        return '0'
    except:
        import urllib
        print('using urllib')
        from urllib import request, error #URLError, HTTPError
        req = request.Request('https://api.github.com/repos/{}/{}/commits?per_page=1'.format(u, r))
        try:
            response = request.urlopen(req)
            resp_ok = True
            the_page = response.read().decode("utf-8")
            i=(the_page.find("message"))
            j=the_page[i+10:].find("\"")
            cmt_msg=the_page[i+10:i+10+j]
            #print(cmt_msg)
            #cmt_msg+="_cmtnum=634" NB all the commits must have commit message ending with _cmtnum=nnn
            k=cmt_msg.find("cmtnum=")
            if k:
                return(cmt_msg[k+7:])
            else:
                return('0')
            # print (int(cmt_msg[k+8:]))
            # print(the_page.find("message"))
            # print(the_page[i+10:].find("\""))
            # print(the_page[i+10:24])
            # print(the_page[i+10:i+10+24])
            
        except error.HTTPError as e:
            FreeCAD.Console.PrintWarning('The server couldn\'t fulfill the request.')
            FreeCAD.Console.PrintWarning('Error code: ' + str(e.code)+'\n')
            return '0'
        except error.URLError as e:
            FreeCAD.Console.PrintWarning('We failed to reach a server.\n')
            FreeCAD.Console.PrintWarning('Reason: '+ str(e.reason)+'\n')        
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