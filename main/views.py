from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from xlutils.copy import copy
from datetime import datetime, date
import os
import xlwt
from  xlwt import Workbook
from xlrd import open_workbook

from .models import *
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
        do_attendance(names, request)

        
        return JsonResponse(names, safe=False)

def get_attendance_data(request):
    
    # path of the file
    path = './media/documents/'+ str(request.user.username)
    todays = date.today()
    file_name = ( str(request.user.username) 
                + str(todays.year) 
                + str(todays.month)
                + '.xls'
                )
    
    # final file path
    file_path = path + '/' + file_name
    
    # read the  file
    rd = open_workbook(file_path)
    s_sheet = rd.sheet_by_index(0)

    # content type of response
    response = HttpResponse(content_type='applicatio/ms-excel')

    # decide file name
    response['Content-Disposition'] = 'attachment; filename="attendance.xls"'

    # creating workbook
    wb = xlwt.Workbook(encoding='utf-8')

    # adding sheet
    ws = wb.add_sheet('sheet1')

    # header style
    style = xlwt.easyxf('font: bold 1') 

    # coping all data from one excel file to new file.
    for row in  range(s_sheet.nrows):
        for col in range(s_sheet.ncols):
            value = s_sheet.cell(row, col).value
            if row == 0:
                ws.write( row, col, value, style)
            
            else:
                ws.write( row, col, value)
    wb.save(response)
    return response


def do_attendance(names, request):
    for name in names:
        paths = './media/documents/'+ str(request.user.username)
        todays = date.today()
        file_name = ( str(request.user.username) 
                    + str(todays.year) 
                    + str(todays.month)
                    + '.xls'
                    )
        file_path = paths + '/' + file_name
        date_pattern = ( str(todays.year) +'-'+ 
                         str(todays.month) +'-'+ 
                         str(todays.day)
                        )
        # using style to bold the name of file heading.
        style = xlwt.easyxf('font: bold 1') 
        if not os.path.isfile(file_path):
            workbook = Workbook()  # open a workbook
            sheet1 = workbook.add_sheet('Sheet 1') 

        
            # writing and style the  heading.
            sheet1.write( 0, 0, 'Name', style ) 
            sheet1.write( 0, 1, 'Employee Id', style ) 
            sheet1.write( 0, 2, 'Total Presence', style )
            sheet1.write( 0, 3, date_pattern, style)
            # save the file.
            all_users = EmployeeInfo.objects.filter( user = request.user ).values('name', 'employee_id')
            index = 1
            while(index < len(all_users)):
                sheet1.write( index, 0, all_users[index]['name'] )
                sheet1.write( index, 1, all_users[index]['employee_id'] )
                sheet1.write( index, 3, "A" )
                index += 1
            workbook.save(file_path)
        else:
            rb = open_workbook(file_path, formatting_info=True )
            r_sheet = rb.sheet_by_index(0) # read only copy to introspect the file    
            cols = r_sheet.ncols
            wb = copy(rb) # a writable copy (I can't read values out of this, only write to it)
            w_sheet = wb.get_sheet(0) # the sheet to write to within the writable copy
            for row in range( r_sheet.nrows ):
                if r_sheet.cell(0, (cols-1)).value != date_pattern:
                    w_sheet.write(0, cols, date_pattern, style)
                    for row_val in range(1, r_sheet.nrows):
                        w_sheet.write(row_val, cols, 'A')
                wb.save(file_path)
                read_book = open_workbook(file_path, formatting_info = True)
                sheet = read_book.sheet_by_index(0)
                cols = sheet.ncols
                condition1 = (sheet.cell(row, 0).value == name)
                condition2 = (sheet.cell(row, cols-1).value == 'A')
            
                if condition1 and condition2 :
                    current_time = datetime.datetime.now().strftime('%H:%M')
                    wb = copy(read_book) 
                    w_sheet = wb.get_sheet(0)
                    w_sheet.write(row, cols-1, current_time)
                    wb.save(file_path)
    
    return 

def add_register_employee_sheet(name, emp_id, request):
    dir_path = './media/documents/'+ str(request.user.username)
    todays_date = date.today()
    file_name = ( str(request.user.username)
                + str(todays_date.year)
                + str(todays_date.month)
                + '.xls'
    )
    file_path = dir_path + '/' + file_name 
    style = xlwt.easyxf('font: bold 1')  
    date_pattern = ( str(todays_date.year) +'-'+ 
                         str(todays_date.month) +'-'+ 
                         str(todays_date.day)
                        )
    
    current_time = datetime.datetime.now().strftime('%H:%M')

    if not os.path.isfile(file_path):
        
        workbook = Workbook()  # open a workbook
        sheet1 = workbook.add_sheet('Sheet 1') 

        # writing and style the  heading.
        sheet1.write( 0, 0, 'Name', style ) 
        sheet1.write( 0, 1, 'Employee Id', style ) 
        sheet1.write( 0, 2, 'Total Presence', style )
        sheet1.write( 0, 3, date_pattern, style )
        # save the file.
        all_users = EmployeeInfo.objects.filter( user = request.user ).values( 'name', 'employee_id' )
        index = 1
        while( index < len(all_users) ):
            sheet1.write( index, 0, all_users[index]['name'] )
            sheet1.write( index, 1, all_users[index]['employee_id'] )
            if all_users[index]['name'] == name:
                sheet1.write( index, 3, current_time)
            else:
                sheet1.write( index, 3, "A" )

            index += 1
        workbook.save(file_path)
    
    else:
        rb = open_workbook(file_path, formatting_info=True )
        r_sheet = rb.sheet_by_index(0) # read only copy to introspect the file    
        cols = r_sheet.ncols
        wb = copy(rb) # a writable copy (I can't read values out of this, only write to it)
        w_sheet = wb.get_sheet(0) # the sheet to write to within the writable copy
        row_no = r_sheet.nrows
        last_column = (str(todays_date.year) + '-' 
                    + str(todays_date.month) + '-'
                    + str(todays_date.day)
                )

        '''
            if we dont have today's date named column stored in the file.
            so, we create a new column atfirst.
        '''
        if r_sheet.cell(0, (cols-1)).value != last_column:
            w_sheet.write(0, cols, last_column, style)
            w_sheet.write( row_no, cols, current_time)
        else:
            w_sheet.write( row_no, (cols-1), current_time)

        w_sheet.write( (row_no), 0, name)
        w_sheet.write( (row_no), 1, emp_id)
        wb.save(file_path)
    
    return True
    
        
