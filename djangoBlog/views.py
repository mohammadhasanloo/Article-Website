from django.shortcuts import render
from django.shortcuts import HttpResponse

def About(request):
    #return HttpResponse("Hello World!")
    return render(request, "About.html")
def Home(request):
    #return HttpResponse("Hello Welcome To Home :)")
    return render(request, "Home.html")
