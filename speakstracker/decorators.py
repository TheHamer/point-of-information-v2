from django.http import HttpResponse
from django.shortcuts import redirect

def unauthenticated_user(view_func):

    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('trakerhome')
        else:
            return view_func(request, *args, **kwargs)
    
    return wrapper_func

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):

            group = None
            t = None
            if request.user.groups.exists():
                #group = request.user.groups.all()[0].name
                group = request.user.groups.all()[0].name
                t = "red"

            if group in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse(f'{allowed_roles} {request.user.groups} {t} {group} {request.user.groups.exists()} you do not have autherisation to view this page')


            return view_func(request, *args, **kwargs)
        return wrapper_func
    return decorator