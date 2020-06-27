from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage

import os, tensorflow
from tensorflow.keras.models import load_model as lm
import PIL, numpy

from datetime import date
import datetime
import csv

from .models import EmployeeInfo, Images
from django.contrib.auth import authenticate, login, logout

from .register import register
from .recognize import recognize as recognizing

model = lm("/var/www/djangomac/facerecognation/models/embedder/facenet.h5")

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
            '''
                all data that has come from fron-end 
                are stored in different different variable
            '''
            files = request.FILES['image']
            name = request.POST['name']
            ids = request.POST['id']
            dob = request.POST['dob']
            gender = request.POST['gender']
            
            # all information is storing in EmployeeInfo table
            information = EmployeeInfo(
                name=name, 
                employee_id= ids,
                Birthday=dob,
                Gender = gender, 
                user=request.user)

            # save to data to db
            information.save()
            term_no=0

            # using while loop for coping 12 pcs image to store in db
            while(term_no < 12):
                image = Images(name_of_employee=information, images = files)
                image.save()
                term_no += 1

            status = register(request.user.username, name)

            add_register_employee_sheet(name, ids, request)
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
        #folder = '/var/www/djangomac/facerecognation/media/documents/'+ str(request.user.username) + "/temp"
        #fs = FileSystemStorage(location=folder)
        #fs.save(files.name, files)
        img = PIL.Image.open(files)
        
        names = recognizing( request.user.username, img, 65, model)
        
       
        do_attendance2(names, request)
        length = len(names)
        reverse_names = []
        for index in  range(length, 0, -1):
            name = names[index-1]
            reverse_names.append(name)
        
        return JsonResponse(reverse_names, safe=False)

def get_attendance_data(request):
    
    # path of the file
    path = '/var/www/djangomac/facerecognation/media/documents/'+ str(request.user.username)
    todays = date.today()
    file_name = ( str(request.user.username) 
                + str(todays.year) 
                + str(todays.month)
                + '.csv'
                )
    
    # final file path
    file_path = path + '/' + file_name
    
    # read the  file
    

    # content type of response
    response = HttpResponse(content_type='text/csv')

    # decide file name
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'
    # creating workbook
    all_rows = []
    with open(file_path, 'r') as csvfile:
        csvread = csv.reader(csvfile)
        for row in csvread:

            all_rows.append(row)
        csvfile.close()
    
    writer = csv.writer(response)
    writer.writerows(all_rows)


    return response


def do_attendance2(names, request):
    for name in names:
        path = '/var/www/djangomac/facerecognation/media/documents/' + str(request.user.username)
        todays = date.today()
        file_name = ( str(request.user.username) 
                    + str(todays.year) 
                    + str(todays.month)
                    + '.csv'
                    )
        file_path = path + '/' + file_name
        date_pattern = ( str(todays.year) +'-'+ 
                         str(todays.month) +'-'+ 
                         str( int(todays.day) )
                        )
        column = ['name', 'id', 'total',  date_pattern]
        employes = EmployeeInfo.objects.filter(
            user = request.user
        ).values('name', 'employee_id')
        
        current_time = datetime.datetime.now().strftime('%H:%M')

        if not os.path.isfile(file_path):
            with open(file_path, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                
                rows = ['',['name', 'id', 'total',  date_pattern]]
                for employee in employes:
                    
                    if name == employee['name']:
                        row = [employee['name'], employee['employee_id'], '1', current_time]
                        rows.append(row)
                    
                    else:
                        row = [employee['name'], employee['employee_id'], '0', 'A']
                        rows.append(row)
                csvwriter.writerows(rows)
                csvfile.close()
        else:
            with open(file_path, 'r+') as csvfile:
                
                csvreader = csv.reader(csvfile)
                
                lists = list(csvreader)
                first_row = lists[1]
                first_row_last_col = first_row[len(first_row) - 1]

                if first_row_last_col != date_pattern:
                    first_row.append(date_pattern)
                    for index in range(2, len(lists)):
                        length = len(lists[index])
                        if lists[index][0] == name:
                            lists[index].append(current_time)
                            total_attendance = int(lists[index][2]) + 1
                            lists[index][2] = total_attendance

                        else:
                            lists[index].append('A')
                    csvfile.close()
                    write_file = open(file_path, 'w', newline='')
                    csv_writer = csv.writer(write_file)
                    csv_writer.writerows(lists)
                    write_file.close()

                else:
                    for index in range(2, len(lists)):
                        length = len(lists[index])
                        if lists[index][0] == name and lists[index][length-1] == 'A':
                            lists[index][length-1] = current_time
                            break

                    csvfile.close()
                    write_file = open(file_path, 'w', newline='')
                    csv_writer = csv.writer(write_file)
                    csv_writer.writerows(lists)
                    write_file.close()
    return
    

def add_register_employee_sheet(name, emp_id, request):
    dir_path = '/var/www/djangomac/facerecognation/media/documents/'+ str(request.user.username)
    todays_date = date.today()
    file_name = ( str(request.user.username)
                + str(todays_date.year)
                + str(todays_date.month)
                + '.csv'
    )
    file_path = dir_path + '/' + file_name 
    date_pattern = ( str( todays_date.year ) +'-'+ 
                         str( todays_date.month ) +'-'+ 
                         str( int(todays_date.day) )
                    )
    
    current_time = datetime.datetime.now().strftime('%H:%M')
    column = ['name', 'id', 'total',  date_pattern]
    employes = EmployeeInfo.objects.filter(
            user = request.user
        ).values('name', 'employee_id')
        
    if not os.path.isfile(file_path):
        
        with open(file_path, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                
                rows = ['',['name', 'id', 'total',  date_pattern]]
                for employee in employes:
                    
                    if name == employee['name']:
                        row = [employee['name'], employee['employee_id'], '1', current_time]
                        rows.append(row)
                    
                    else:
                        row = [employee['name'], employee['employee_id'], '0', 'A']
                        rows.append(row)
                csvwriter.writerows(rows)
                csvfile.close()
    
    else:
        with open(file_path, 'r+') as csvfile:
                print('I have file')
                csvreader = csv.reader(csvfile)
                
                lists = list(csvreader)
                first_row = lists[1]
                first_row_last_col = first_row[len(first_row) - 1]

                if first_row_last_col != date_pattern:
                    print('i do not have todays date')
                    first_row.append(date_pattern)
                    for index in range(2, len(lists)):
                        # length = len(lists[index])
                        # if lists[index][0] == name:
                        #     lists[index].append(current_time)
                        #     total_attendance = int(lists[index][2]) + 1
                        #     lists[index][2] = total_attendance

                        # else:
                        lists[index].append('A')

                    csvfile.close()
                    instance = []
                    for val in first_row:
                        print(val)
                        if val == 'name':
                            instance.append(name)
                        elif val == 'id':
                            instance.append(emp_id)
                        elif val == 'total':
                            instance.append(1)
                        elif val == date_pattern:
                            instance.append(current_time)
                        else:
                            instance.append('-')
                    
                    lists.append(instance)
                    write_file = open(file_path, 'w', newline='')
                    csv_writer = csv.writer(write_file)
                    csv_writer.writerows(lists)
                    write_file.close()

                else:
                    instance =[]
                    for val in first_row:
                        if val == 'name':
                            instance.append(name)
                        elif val == 'id':
                            instance.append(emp_id)
                        elif val == 'total':
                            instance.append(1)
                        elif val == date_pattern:
                            instance.append(current_time)
                        else:
                            instance.append('-')
                    lists.append(instance)
                    csvfile.close()
                    write_file = open(file_path, 'w', newline='')
                    csv_writer = csv.writer(write_file)
                    csv_writer.writerows(lists)
                    write_file.close()
    return