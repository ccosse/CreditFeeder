# -*- coding: UTF-8 -*-
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required,user_passes_test

import os,logging,time,json,sys
import xmlrpc.client

FORMAT = 'VIEW: %(message)s'

RLOG_FULL_PATH='/var/www/feeder/creditfeeder/feeder.log'
logging.basicConfig(filename=RLOG_FULL_PATH,level=logging.DEBUG, format=FORMAT)
mylogger=logging

def logout_view(request):
    logging.debug("logout_view")
    empty_session_id=logout(request)
    logging.debug("empty_session_id: %s"%empty_session_id)
    request.session.delete()
    return HttpResponseRedirect("/")

def home(request):
	logging.debug("home");
	if request.user.is_authenticated():
		logging.debug("already authenticated:"+request.user.username)
		if request.user.userprofile.is_parent==True:
			return parent_app(request,request.user.username,{})
		return student_app(request,request.user.username,{})

	ip=request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
	logging.debug("not authenticated: %s"%(ip))
	if request.method == 'POST':
		mylogger.debug("getting login_pyld from post ...")
		mylogger.debug(request.POST["login_pyld"])
		pyld=json.loads(request.POST["login_pyld"])
		uname=None
		acct=None
		try:
			uname=pyld['device_ip']+"_STUDENT"
			if pyld['account_type']=="parent":uname=pyld['device_ip']+"_PARENT"
			acct=User.objects.get(username=uname)
			mylogger.debug("got user")
			login(request,acct)
			mylogger.debug("logged-in user "+uname)

		except:
			mylogger.debug("creating new account ...")
			uname=pyld['device_ip']+"_STUDENT"
			if pyld["account_type"]=="parent":uname=pyld['device_ip']+"_PARENT"
			acct=User.objects.create_user(username=uname,password='pycon2017')
			acct.userprofile.is_parent=False
			if pyld["account_type"]=="parent":acct.userprofile.is_parent=True
			acct.userprofile.save()
			acct.save()

			mylogger.debug("logging-in "+uname)
			login(request,acct)

		if acct.userprofile.is_parent==True:
			return parent_app(request,uname,pyld)

		return student_app(request,uname,pyld)

	context={
		'title':'Credit Feeder Login',
		'device_ip':ip,
	}
	return render(
		request,'device-login.html',
		context
	)

def get(request):
	progress=0
	try:
		logging.debug("get request")
		logging.debug(request)
		qs=request.META['QUERY_STRING']
		logging.debug(qs)
		if len(qs)>1:
			logging.debug(qs)
			split_qs=qs.split("&")
			action=split_qs[0].split('=')[1]
			u=split_qs[1].split('=')[1]
			p=split_qs[2].split('=')[1]
			user = authenticate(username=u, password=p)
			if user!=None:return HttpResponse(user.userprofile.credit_balance)
			else:return HttpResponse('Login Failed')
	except:
		return HttpResponse('Exception')
	return HttpResponse('What Happened?');


@login_required
def student_app(request,username,pyld):
	context={
		'title':'Student@CreditFeeder',
		'username':username,
		'credit_balance':request.user.userprofile.credit_balance,
		'json_pyld':json.dumps(pyld),
	}
	return render(request,'student_app.html',context)

@login_required
def parent_app(request,username,pyld):
	context={
		'title':'Parent@CreditFeeder',
		'username':username,
		'json_pyld':json.dumps(pyld),
	}
	return render(request,'parent_app.html',context)
