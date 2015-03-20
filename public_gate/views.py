from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.core import serializers
from django.contrib.auth.hashers import (
    make_password)
from OpenMDM import settings
import os




from public_gate.models import PropertyList, PropertyListForm, UserForm, Address, Test, RecipeForm, Plist


def home(request):
    """
    Displays home page
    :param request:
    :return render:
    """
    test = Test(username="Romain", date_inscription="2014-07-07", address=Address(city="Paris", street="Water street", zip="75016"))
    test.save()
    d = {}
    return render(request, 'public_gate/home.html', d)


def about(request):
    """
    Displays about page
    :param request:
    :return render:
    """
    d = {}
    return render(request, 'public_gate/about.html', d)


def contact(request):
    """
    Displays contact page
    :param request:
    :return render:
    """
    d = {}
    return render(request, 'public_gate/contact.html', d)


########################################################################
#                                                                      #
#                       Authentication Views
#                                                                      #
########################################################################


def site_login(request):
    """
    Logs in current user
    :param request:
    :return render:
    """
    if request.method == "POST":
        user = None
        user_login = request.POST['login']
        user_password = request.POST['password']
        if user_login != "" and user_password != "":
            user = authenticate(username=user_login, password=user_password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('public_gate:home'))
        else:
            # User.objects.create_user(user_login, '', user_password).save()
            return render(request, 'public_gate/home.html', {"error_message": "Wrong login/password combination"})
    return render(request, 'public_gate/home.html', {"error_message": "One or more fields are empty"})


def site_logout(request):
    """
    Logs out current user
    :param request:
    :return render:
    """
    logout(request)
    return HttpResponseRedirect(reverse('public_gate:home'))


########################################################################
#                                                                      #
#                       Property List Views
#                                                                      #
########################################################################


def property_lists(request):
    """
    Fetches all property lists
    From: property_list/
    :param request: 
    :return render:
    """
    property_lists = PropertyList.objects.order_by('id')
    return render(request, 'public_gate/property_lists.html', dict(property_lists=property_lists))


def property_lists_for_user(request):
    """
    Fetches plists for specific user
    From: user/<user_id>/property_list/
    :param request:
    :param user_id:
    :return render:
    """
    property_lists = {}
    if settings.RETRIEVE_PLIST_FROM_GROUPS == "all":
        groups = request.user.ldap_user.group_names
    else:
        groups = {request.user.ldap_user.attrs['gidnumber'][0]}
    for group in groups:
        plists = Plist.objects(group_name=group)
        if len(plists) > 0:
            for plist in plists:
                plist.id = str(plist.id)
                print(plist.id)
            property_lists[group] = Plist.objects(group_name=group)
        print(property_lists)

    return render(request, 'public_gate/property_lists.html', dict(property_lists=property_lists))


def property_list_detail(request, plist_id):
    """
    Fetches one plist
    From: property_list/<plist_id>/
    :param request: 
    :param plist_id: 
    :return render:
    """
    try:
        plist = PropertyList.objects.get(id=plist_id)
        dependencies = plist.get_dependent_properties()
    except PropertyList.DoesNotExist:
        return HttpResponse(status=404)
    plist_python = serializers.serialize("python", [plist])
    dependencies_json = serializers.serialize("python", dependencies)
    return render(request, 'public_gate/property_list_detail.html', dict(plist=plist,
                                                                         dependencies=dependencies,
                                                                         plist_python=plist_python,
                                                                         dependencies_json=dependencies_json))


def property_list_download(request, plist_id):
    """
    Fetches one plist and converts it to plist format (xml based)
    From: property_list/<plist_id>/download/
    :param request: 
    :param plist_id: 
    :return:
    """
    try:
        plist = Plist.objects(id=plist_id)
        plist = plist[0].generate()
    except PropertyList.DoesNotExist:
        return HttpResponse(status=404)
    return render(request, 'public_gate/property_list_download.html', dict(plist=plist), content_type="application/xml")


def add_property_list(request):
    """
    Adds one property list
    From: property_list/add/
    :param request:
    :return:
    """
    form = False
    files = False
    if request.method == 'POST' and "file" in request.POST:
        form = RecipeForm(request.POST.get('file')).html_output()
    else:
        if request.method == 'POST':
            # We save the plist
            form = RecipeForm(recipe_name="recipe.plist",
                              data=request.POST)
            form.save()

        # We display all the recipes available
        files = []
        for file in os.listdir(os.path.dirname(__file__) + "/../recipe"):
            if file.endswith(".plist"):
                files.append(file)
    return render(request, 'public_gate/property_list_add.html', dict(files=files,
                                                                      form=form))