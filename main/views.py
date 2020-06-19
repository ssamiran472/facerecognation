from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

import os
from datetime import date
import datetime
import csv

from .models import EmployeeInfo, Images
from django.contrib.auth import authenticate, login, logout
# from .register import register

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
            # status = register.register(request.user.username, name)
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
        names=['samiran']
        do_attendance2(names, request)

        
        return JsonResponse(names, safe=False)

def get_attendance_data(request):
    
    # path of the file
    path = './media/documents/'+ str(request.user.username)
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
        path = './media/documents/' + str(request.user.username)
        todays = date.today()
        file_name = ( str(request.user.username) 
                    + str(todays.year) 
                    + str(todays.month)
                    + '.csv'
                    )
        file_path = path + '/' + file_name
        date_pattern = ( str(todays.year) +'-'+ 
                         str(todays.month) +'-'+ 
                         str(todays.day)
                        )
        column = ['name', 'id', 'total',  date_pattern]
        employes = EmployeeInfo.objects.filter(
            user = request.user
        ).values('name', 'employee_id')
        
        current_time = datetime.datetime.now().strftime('%H:%M')

        if not os.path.isfile(file_path):
            with open(file_path, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(column)
                rows = []
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
                first_row = next(csvreader, 0)
                print(csvreader)
                first_row_last_col = first_row[len(first_row) - 1]

                if first_row_last_col != date_pattern:
                    first_row.append(date_pattern)
                    for row in csvreader:
                        if name == row[0]:
                            row.append(current_time)
                        else:
                            row.append('A')
                    
                else:
                    for row in csvreader:
                        names=row[0]
                        attendance_val = row[len(row) - 1]
                        if name == names and attendance_val == 'A':
                            row[attendance_val] = current_time
                csvfile.close()
    return




def add_register_employee_sheet(name, emp_id, request):
    dir_path = './media/documents/'+ str(request.user.username)
    todays_date = date.today()
    file_name = ( str(request.user.username)
                + str(todays_date.year)
                + str(todays_date.month)
                + '.csv'
    )
    file_path = dir_path + '/' + file_name 
    date_pattern = ( str( todays_date.year ) +'-'+ 
                         str( todays_date.month ) +'-'+ 
                         str( todays_date.day )
                    )
    
    current_time = datetime.datetime.now().strftime('%H:%M')
    column = ['name', 'id', 'total',  date_pattern]
    employes = EmployeeInfo.objects.filter(
            user = request.user
        ).values('name', 'employee_id')
        
    if not os.path.isfile(file_path):
        
        with open(file_path, 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(column)
                rows = []
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
        new_arr = []
        with open(file_path, 'r') as csvfile:
            
            
            csvreader = csv.reader(csvfile)

            # extracting field names through first row 
            first_row = next(csvreader) 
            
            first_row_last_col = first_row[len(first_row) - 1]
           
            
            if first_row_last_col != date_pattern:
                first_row.append(date_pattern)
                for col in first_row:
                    if col == 'name':
                        new_arr.append(name)
                    elif col == 'id':
                        new_arr.append(emp_id)
                    elif col == 'total':
                        new_arr.append('1')
                    elif col == date_pattern:
                        new_arr.append(current_time)
                    else:
                        new_arr.append('-')
            else:
                for col in  first_row:
                    if col == 'name':
                        new_arr.append(name)
                    elif col == 'id':
                        new_arr.append(emp_id)
                    elif col == 'total':
                        new_arr.append('1')
                    elif col == date_pattern:
                        new_arr.append(current_time)
                    else:
                        new_arr.append('-')

                
                csvfile.close()
        
        with open(file_path, 'a+', newline='') as csvfile:
            csv_write = csv.writer(csvfile)
            csv_write.writerow(new_arr)
            csvfile.close()

    return