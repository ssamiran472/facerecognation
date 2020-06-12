from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.contrib.auth import authenticate, login, logout
from datetime import datetime
# from .register import register
import time

@login_required(login_url="/login/")
def index(request):
    # redirect to index page or deshbord page
    return render(request, 'index.html')


def logins(request):
    # if request method is post so go in it and chack for authentication and login process. 
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        # authenticate the user
        user = authenticate(request, username=username, password=password)
        if user:
            # if all data that is username and password is matched so login the user.
            print(user)
            login(request, user)
            # some one  tried to go dashbord page without login so redirect to login page
            if request.GET.get('next', None):
                # after login redirect to that page where they want to go.
                return HttpResponseRedirect(request.GET['next'])
            return HttpResponseRedirect(reverse('index_page'))
        else:
            # for wrong data provided or something happen wrong go to login page
            return render(request, 'login.html')
    # for get request render to login page.
    return render(request, 'login.html')


@login_required(login_url='/login/')
@csrf_exempt
def registering(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    elif request.method == 'POST':
        if request.FILES['image']:
            files = request.FILES['image']
            name = request.POST['name']
            ids = request.POST['id']
            dob = request.POST['dob']
            print('dob', type(dob))
            # dob=datetime.strptime(dob, '%m/%d/%y')
            gender = request.POST['gender']
            # print(files, name, ids, dob, gender)
            # print(files, name, ids, dob, gender)
            information = EmployeeInfo(
                name=name, 
                employee_id= ids,
                Birthday=dob,
                Gender = gender, 
                user=request.user)
            information.save()
            term_no=0
            while(term_no < 12):
                image = Images(name_of_employee=information, images = files)
                image.save()
                term_no += 1
            # status = register.register(request.user.username, name)
            # print(status)
        return JsonResponse({'success': 'file uploaded successful'}, safe=False)

# logout.
@login_required(login_url="/login/")
def loging_out(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))


@login_required(login_url='/login/')
def recognize(request):
    if request.method == 'GET':
        try:
            del request.session['checking_success']
            request.session['checking_success']='success'
        except KeyError:
            return HttpResponseRedirect(reverse('extra_checking'))
        return render(request, 'recognize2.html')

# extra checking for go to recognation page
def secoend_time(request):
    if request.method == "POST":
        # taking the value for login in variable
        passwords = request.POST['password']
        
        user = authenticate(request, username = request.user.username, password = passwords)
        if user is not None:
            if user.id == request.user.id:
                request.session['checking_success'] = 'success'
                return HttpResponseRedirect(reverse('recognize'))
            else:
                return HttpResponseRedirect(reverse('index.html'))
        else:
            return HttpResponseRedirect(reverse('index_page'))
    else:
        return HttpResponseRedirect(reverse('index_page'))


@csrf_exempt
def recognizing_image(request):
    if request.method == 'POST':
        files = request.FILES['images']
        print('file', files)
    time.sleep(3)
    return JsonResponse(['samiran'], safe=False)
