from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm,MyUserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required #this decorator is used to restrict some of the pages from accessing without loggin in, like creating and updating rooms and redirecting them to the login or singup page.

# Create your views here.
def index(request):
    q=request.GET.get('q') if request.GET.get('q') != None else ''
    # rooms = Room.objects.filter(topic__name__icontains = q) #topic__name__icontains this basically helps in searching eg if we search for python and type py it looks that it matches and shows the result for python.
    # a better feature would be for a user to be able to search by the topic or the title or the description of the room.in order to do so, we import query q and then put some or conditions.
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    ) 
    room_count = rooms.count()
    room_messages= Message.objects.filter(Q(room__topic__name__icontains=q)) #this will make sure that the activity field contains the activities related to those topics only
    topics = Topic.objects.all()[0:3]
    context = {'rooms':rooms, 'topics':topics, 'room_count':room_count,'room_messages':room_messages}
    return render(request,'chatapp/home.html',context)

def room(request,pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all() #basically we are saying to give the child messages of the parent room
    participants = room.participants.all()

    if request.method == "POST":
        message=Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body'),#getting the body of the input form with name 'body'.
        )
        room.participants.add(request.user)
        return redirect('room',pk=room.id)

    context = {'room':room,'room_messages':room_messages,'participants':participants} 
    return render(request,'chatapp/room.html',context)

#now we are gonna create CRUD functionalities for the user to create room connecting to room_form template.
@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name) # this basically means when a user selects the already existent topic then created becomes false but if user enters new topic then it gets in created variable
        Room.objects.create(
            host = request.user,
            topic= topic,
            name = request.POST.get('name'),
            description = request.POST.get('description')
        )
        return redirect('index')

    context = {'form':form, 'topics':topics}
    return render(request,'chatapp/room_form.html',context)


@login_required(login_url='login')
def updateRoom(request,pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    # till now anybody can just enter the id of the room and update. we must ensure that only room user can do so.
    if request.user != room.host:
        return HttpResponse("You are not allowed to do so.") 
    if request.method == "POST":
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name) # this basically means when a user selects the already existent topic then created becomes false but if user enters new topic then it gets in created variable
        room.name = request.POST.get('name')
        room.description = request.POST.get('description')
        room.topic = topic
        room.save() 
        return redirect('index')
    context = {'form':form , 'topics':topics, 'room':room}
    return render(request,'chatapp/room_form.html',context)

@login_required(login_url='login')
def deleteRoom(request,pk):
    room = Room.objects.get(id=pk)
    if request.method == "POST":
        room.delete()
        return redirect('index')
    return render(request,'chatapp/delete.html',{'obj':room})


def loginPage(request):
    page= 'login'
    #we need to make sure that if the user is already logged in then redirect them to home
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == "POST":
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        #checking if the user exists
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request,'User doesnot exist!')

        user = authenticate(request, email=email,password=password)

        if user is not None:
            login(request,user)
            return redirect('index')
        else:
            messages.error(request,'Invalid email or Password')
    context = {'page':page}
    return render(request,'chatapp/login_register.html',context)

def logoutUser(request):
    logout(request)
    return redirect('index')

def registerPage(request):
    form = MyUserCreationForm()
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) # we dont want to create the user right away to lowercase the username.
            user.username = user.username.lower()
            user.save()
            #we are gonna log the user in and redirect to home page after registration.
            login(request,user)
            return redirect('index')
        else:
            messages.error(request,'User registration invalid!')
    context= {'form':form}
    return render(request,'chatapp/login_register.html',context)

@login_required(login_url='login')
def deleteMessage(request,pk):
    message = Message.objects.get(id=pk)
    if request.user != message.user:
        return HttpResponse('You are not allowed here!')
    if request.method == "POST":
        message.delete()
        return redirect('index')
    return render(request,'chatapp/delete.html',{'obj':message})

def userProfile(request,pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all() #getting all the rooms of a particular user when viewing the profile
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context={'user':user, 'rooms':rooms, 'topics':topics, 'room_messages':room_messages}
    return render(request,'chatapp/profile.html',context)

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)
    if request.method == "POST":
        form = UserForm(request.POST,request.FILES,instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    return render(request,'chatapp/update-user.html', {'form':form})
    

def topicsPage(request):
    q=request.GET.get('q') if request.GET.get('q') != None else ''
    topics= Topic.objects.filter(name__icontains=q)
    return render(request,'chatapp/topics.html',{'topics':topics})

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request,'chatapp/activity.html',{'room_messages':room_messages})