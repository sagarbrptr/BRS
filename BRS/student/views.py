# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import connection, transaction
from django.shortcuts import render, render_to_response,redirect
from django.http import HttpResponse
# import mysql.connector
from django.template import RequestContext

# from student.models import *
from django.contrib.auth import authenticate, login, logout 
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


class DB:

    def __init__(self):
        self.cursor = connection.cursor()

    def __del__(self):
        self.cursor.close()
        connection.close()

    def beginTransaction(self):

        try:
            self.cursor.execute("set autocommit = off;")
        except:
            print("Error in setting autocommit off")
            return False

        try:
            self.cursor.execute("begin;")
        except:
            print("Error in beginning transaction")
            return False

        return True

    def rollback(self):

        try:
            self.cursor.execute("rollback;")
        except:
            print("Error in rolling back")
            return False

        try:
            self.cursor.execute("set autocommit = on;")
        except:
            print("Error in setting autocommit on")
            return False

        return True

    def commit(self):

        try:
            self.cursor.execute("commit;")
        except:
            print("Error in commiting")
            return False

        try:
            self.cursor.execute("set autocommit = on;")
        except:
            print("Error in setting autocommit on")
            return False

        return True

    def select(self, query, errorMsg):
        try:
            self.cursor.execute(query)

        except:
            print(errorMsg)
            return False

        row = self.cursor.fetchall()
        return row

    def insertOrUpdateOrDelete(self, query, errorMsg):
        try:
            self.cursor.execute(query)
        except:
            print(errorMsg)
            return False

        return True

@login_required(login_url="/login")
def studentHome(request):

    userCardnumber = ""
    if request.user.is_authenticated():
        userCardnumber = request.user.username

    database = DB()

    books_db = "select distinct b.title, b.barcode, t.DATE from books_db as b, transaction as t where b.barcode = t.barcode and t.cardnumber = '" + userCardnumber + "' group by title;"
    query = "select distinct b.title, b.barcode, t.DATE " + "from books as b, transaction as t" + \
        " where b.barcode = t.barcode and t.cardnumber = '" + userCardnumber + "' group by title union all " + books_db
    errorMsg = "Error in selecting from books_db or books"
    # print(query)

    row = database.select(query, errorMsg)

    if not len(row):     # If no book is issued, return
        context = {
            'noBookIssued': True
        }
        return render(request, 'student/issue-history.html', context)

    result = []

    for i in row:

        temp = {}
        temp["title"] = str(i[0])
        temp["barcode"] = str(i[1])
        temp["DATE"] = str(i[2])

        query_get_rating = "select rating,valid from ratings where barcode = (select bt.barcode from bt_map bt where bt.title ='" + \
            temp["title"] + "' limit 1) and cardnumber = '" + userCardnumber + "';"
        errorMsg = "Error in selecting rating from ratings"

        res = database.select(query_get_rating, errorMsg)

        if res :
            temp["rating"] = res[0][0]
            temp["valid"] = res[0][1]        

        result.append(temp)

    context = {
        'noBookIssued': False,
        'result': result
    }

    return render(request, 'student/issue-history.html', context)

def increaseRequestCount(database, request, userCardnumber, srNo):

    alreadyRequested = False
    newRequest = True
    failMsg = ""
    successMsg = ""

    # Check if user has already requested the book
    # By inserting in bookRequest table directly
    # If inserted, then not requested earlier, otherwise requested

    # Insert vote in bookRequest table cardnumber needed
    insertQuery = "insert into bookRequest (srNo, cardnumber) values ('" + \
        srNo + "', '" + userCardnumber + "');"
    errorMsg = "Error in inserting bookRequest"

    insertSuccessful = database.insertOrUpdateOrDelete(
        insertQuery, errorMsg)

    # If insertion failed, rollback
    if not insertSuccessful:
        alreadyRequested = True
        newRequest = False
        failMsg = "You have already requested for this book"
        database.rollback()

    # Else if insertion successful, update requestCount in libraryRecommendation
    if not alreadyRequested:  # Update requestCount
        updateQuery = "update libraryRecommendation set requestCount = requestCount + 1 where srNo = '" + srNo + "';"
        errorMsg = "Error in updating libraryRecommndation"

        updateSucessful = database.insertOrUpdateOrDelete(
            updateQuery, errorMsg)

        # If update not successful, rollback
        if not updateSucessful:
            failMsg = "Error in updating requestCount"
            database.rollback()

    # If nothing failed, commit
    if not failMsg:
        successMsg = "New Book Recommended"
        database.commit()
    
    return alreadyRequested, newRequest, failMsg, successMsg

@login_required(login_url="/login")
def recommendLibrary(request):

    userCardnumber = ""
    if request.user.is_authenticated():
        userCardnumber = request.user.username

    libraryResult = []
    title = ""
    searchBook = True
    blankSearch = True
    alreadyRecommendedResult = []  # Turns on if user checks already recommended books
    checkRecommendedBooks = False
    newBookRecommendation = False  # Turns on when user wants to recommend new book
    newBookRecommended = False
    newTitle = ""
    newAuthor = ""
    newCategory = ""
    hiddenTitle = ""  # Needs to be fixed
    hiddenTitle1 = ""  # Needs to be fixed
    newRequest = "False"
    alreadyRequested = "False"
    successMsg = ""
    failMsg = ""

    database = DB()

    if request.POST.get('title'):
        searchBook = False
        blankSearch = False
        checkRecommendedBooks = False
        newBookRecommendation = False
        newBookRecommended = False

        title = request.POST.get('title')

        queryBooks = "select barcode, title from bt_map where title like '%" + \
            title + "%' group by title;"
        errorMsg = "Error in selecting from bt_map"

        row = database.select(queryBooks, errorMsg)

        # If there exists any row, iterate
        if row:
            for i in row:

                temp = {}
                temp["barcode"] = str(i[0])
                temp["title"] = str(i[1])

                if temp['barcode'].find("DB") > 0:      # barcode contains DB
                    queryAuthor = "select author from books_db where barcode = '" + \
                        temp['barcode'] + "' ;"

                else:
                    queryAuthor = "select author from books where barcode = '" + \
                        temp['barcode'] + "' ;"
                errorMsg = "Error in selecting author from books_db or books"

                author = database.select(queryAuthor, errorMsg)
                if not author:
                    temp['author'] = "Not Available"

                else:
                    temp['author'] = str(author[0][0])

                libraryResult.append(temp)



    if request.POST.get('checkRecommendedBooks'):   # Check already Recommended books
        searchBook = False
        checkRecommendedBooks = True
        newBookRecommendation = False
        newBookRecommended = False

        # hiddenTitle is temp, actually should be title
        hiddenTitle = request.POST.get("hiddenTitle")

        query = "select srNo, bookTitle, author, requestCount from libraryRecommendation where bookTitle like '%" + \
            hiddenTitle + "%' group by bookTitle, author;"
        errorMsg = "error in selecting from libraryRecommendation"

        row = database.select(query, errorMsg)

        # If any row, iterate
        if row:
            for i in row:

                temp = {}
                temp["srNo"] = str(i[0])
                temp["title"] = str(i[1])
                temp["author"] = str(i[2])
                temp["requestCount"] = str(i[3])

                alreadyRecommendedResult.append(temp)

    if request.POST.get('newBookRecommendation'):   # Recommend new book

        hiddenTitle1 = request.POST.get('hiddenTitle1')

        newBookRecommendation = True
        searchBook = False
        checkRecommendedBooks = False

    if request.POST.get('newBookSubmit'):   # New book info is submitted        

        newBookRecommendation = True
        searchBook = False
        checkRecommendedBooks = False
        newBookRecommended = True
        alreadyRequested = False

        newTitle = str(request.POST.get('newTitle')).lower()
        newAuthor = str(request.POST.get('newAuthor')).lower()
        newCategory = str(request.POST.get('newCategory')).lower()

        # Start Transaction
        database.beginTransaction()

        # check if same author and title already exists
        query = "select * from libraryRecommendation where bookTitle = '" + \
            newTitle + "' and author = '" + newAuthor + "';"
        errorMsg = "Error in selecting in libraryRecommendation"

        row = database.select(query, errorMsg)
        
        if row:
            if not len(row):    # does not exists,  new Book is recommended
                newRequest = True

                #insert in libraryRecommendation
                insertQuery = "insert into libraryRecommendation values(default, '" + \
                    newTitle + "', '" + newAuthor + "', '" + newCategory + "', 1);"
                errorMsg = "Error in inserting in libraryRecommendation"

                # If insert in libraryRecommendation sucessful,
                # select latest srNo of book inserted
                if database.insertOrUpdateOrDelete(insertQuery, errorMsg):

                    getSrNo = "select max(srNo) from libraryRecommendation ;"
                    errorMsg = "Error in selecting max srNo from libraryRecommendation"

                    latestSrNo = database.select(getSrNo, errorMsg)                

                    # If valid srNo found, insert in bookRequest
                    if latestSrNo:
                        srNo = str(latestSrNo[0][0])
                        insertQuery = "insert into bookRequest (srNo, cardnumber) values ('" + \
                            srNo + "', '" + userCardnumber + "');"
                        errorMsg = "Error in inserting bookRequest"

                        insertSuccessful = database.insertOrUpdateOrDelete(
                            insertQuery, errorMsg)

                        # If insertion failed, rollback
                        if not insertSuccessful:
                            alreadyRequested = True
                            newRequest = False
                            failMsg = "Error in insertion in bookRequest"
                            database.rollback()

                        # Else insertion was successful, commit
                        if not failMsg:
                            successMsg = "New Book Recommended Successfully"
                            database.commit()

                    # Else error in srNo, rollback
                    else:
                        print("Error in selecting srNo from libraryRecommendation")
                        failMsg = "Error in selecting srNo from libraryRecommendation"
                        database.rollback()

                # Else error in insertion in libraryRecommendation
                else:
                    print("Error in insertion in libraryRecommendation")
                    failMsg = "Error in inserting libraryRecommendation"
                    database.rollback()

            # Else book already exists, increase count
            else:
                srNo = str(row[0][0])
                alreadyRequested,  newRequest, failMsg, successMsg = increaseRequestCount(
                    database, request, userCardnumber, srNo)
        
        else:
            failMsg = "Error in title. Check if you have not inserted any quotes!! (-_-)"
    
    if request.POST.get("increaseRequestCount"):
        newBookRecommended = True
        srNo = request.POST.get("increaseRequestCount")

        database.beginTransaction()

        alreadyRequested,  newRequest, failMsg, successMsg = increaseRequestCount(
                database, request, userCardnumber, srNo)


    context = {
        'searchBook': searchBook,
        'libraryResult': libraryResult,
        'blankSearch': blankSearch,
        'alreadyRecommendedResult': alreadyRecommendedResult,
        'checkRecommendedBooks': checkRecommendedBooks,
        'newBookRecommendation': newBookRecommendation,
        'newTitle': newTitle,
        'newAuthor': newAuthor,
        'newCategory': newCategory,
        'newBookRecommended': newBookRecommended,
        'title': title,
        'alreadyRequested': alreadyRequested,
        'newRequest': newRequest,
        'failMsg': failMsg,
        'successMsg': successMsg,
        'hiddenTitle': hiddenTitle,     # Needs to be fixed
        'hiddenTitle1': hiddenTitle1
    }
    return render(request, 'student/recommend-library.html', context)

@login_required(login_url="/login")
def studentRecommendation(request):

    result = []

    context = {
        'result': result
    }
    return render(request, 'student/recommend-student.html', context)
