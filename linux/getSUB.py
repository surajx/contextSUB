#!/usr/bin/python
import xmlrpclib
import sys
import struct, os
import base64
import zlib

def hashFile(name): 
    ''' Returns hash of a video file.
        Taken from OpenSubtitles:
        http://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
    '''
    try:
        longlongformat = 'q'  # long long
	bytesize = struct.calcsize(longlongformat)
	f = open(name, "rb")
	filesize = os.path.getsize(name)
	hash = filesize
	if filesize < 65536 * 2:
	    return "SizeError"
	for x in range(65536/bytesize):
	    buffer = f.read(bytesize)
	    (l_value,)= struct.unpack(longlongformat, buffer)
	    hash += l_value
	    hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number
	f.seek(max(0,filesize-65536),0)
	for x in range(65536/bytesize):
	    buffer = f.read(bytesize)
	    (l_value,)= struct.unpack(longlongformat, buffer)
	    hash += l_value
	    hash = hash & 0xFFFFFFFFFFFFFFFF
	f.close()
	returnedhash =  "%016x" % hash
	return returnedhash
    except(IOError):
        return "IOError"

def downloadSUB(vidFILE,myproxy,mytoken,sub):
    down_resp=myproxy.DownloadSubtitles(mytoken,[sub['subid']])
    sub_data=zlib.decompress(base64.standard_b64decode(down_resp['data'][0]['data'].encode('ascii')), 15 + 32)
    with open('.'.join(vidFILE.split('.')[:-1])+'.'+sub['sub_fmt'],'w') as subWrite:
        subWrite.write(sub_data)

FILE_PATH=sys.argv[1]
if not FILE_PATH:
    sys.exit('No Atrgument received')
srv_proxy= xmlrpclib.ServerProxy('http://api.opensubtitles.org/xml-rpc')
login_resp= srv_proxy.LogIn('','','en','OS Test User Agent')
try:
    file_hash= hashFile(FILE_PATH)
    file_size= os.path.getsize(FILE_PATH)
    subtitle_req_dict={'sublanguageid':'eng','moviehash':file_hash,'moviebytesize':file_size}
    search_resp= srv_proxy.SearchSubtitles(login_resp['token'],[subtitle_req_dict])
    if not search_resp['data']:
        chk_hash_resp=srv_proxy.CheckMovieHash(login_resp['token'],[file_hash])
        file_hash=chk_hash_resp['data'][file_hash]['MovieHash']
        subtitle_req_dict={'sublanguageid':'eng','moviehash':file_hash}
        search_resp=srv_proxy.SearchSubtitles(login_resp['token'],[subtitle_req_dict])
    sub_list=[]
    for subs in search_resp['data']:
        sub_dict={}
        sub_dict['movie']=subs['MovieReleaseName']
        sub_dict['link']=subs['ZipDownloadLink']
        sub_dict['user']=subs['UserNickName']
        sub_dict['rank']=subs['UserRank']
        sub_dict['subid']=subs['IDSubtitleFile']
        sub_dict['sub_fmt']=subs['SubFormat']
        sub_list.append(sub_dict)
    sub_index=0
    cnt=0
    for sub in sub_list:
        if sub['sub_fmt']=='srt':
            sub_index=cnt
            break
        cnt+=1
    #TODO:Create UI and pass the selected subID to downloadSUB
    downloadSUB(FILE_PATH,srv_proxy,login_resp['token'],sub_list[sub_index])#Asuming that 0 is the selected SUB
    srv_proxy.LogOut(login_resp['token'])
except:
    srv_proxy.LogOut(login_resp['token'])
