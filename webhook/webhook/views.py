#coding=utf-8
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def payload(request) :
    if request.method == 'POST' :
        raw_json_data = request.body
        print(type(raw_json_data))
        print( "%s" %raw_json_data )
        json_obj = json.loads(raw_json_data)
        print(type(json_obj))
        print("%s" %json_obj)
        return HttpResponse("received JSON")
    return HttpResponse("Hello Github")