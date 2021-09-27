from django.contrib.auth import authenticate, login, logout
from django.core.checks import messages
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.http.request import RAISE_ERROR
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import User, Listing, Bid, Comment, Watchlist
from django import forms
from . import util


class NewListingForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput)
    description = forms.CharField(widget=forms.Textarea)
    starting_bid = forms.IntegerField(label="Starting Price:")
    category = forms.CharField(widget=forms.TextInput)


class BiddingForm(forms.Form):
    bid = forms.IntegerField(label="Your bid:")


class AddCommentsForm(forms.Form):
    comments = forms.CharField(widget=forms.Textarea, label="")


categories = Listing.objects.values_list('category', flat=True)


def index(request):
    listings = Listing.objects.all()

    return render(request, "auctions/index.html", {
        "listings": listings,
        "categories": categories
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):

    if request.method == "POST":

        # get the user
        seller = request.user

        # get the listing data from the forms
        title = request.POST['title']
        description = request.POST['description']
        starting_bid = request.POST['starting_bid']
        category = request.POST['category']
        listing = Listing(title=title, description=description,
                          starting_bid=starting_bid, user=seller, category=category)

        # TODO validate the data & error checking
        listing.save()
        return HttpResponseRedirect(reverse('index'))

    else:

        return render(request, "auctions/newlisting.html", {
            "new_listing_form": NewListingForm(),

        })


@login_required
def home(request, id):

    # Request watchlist of the user
    watchlist = util.get_watchlist(id)

    # Request listings of this user
    listings = util.get_listings(id)

    # if the result is not None
    if listings:
        listings_active = []
        listings_ended = []
    # get the objects
    for id in listings_id:
        if id is not None:
            listing = Listing.objects.get(id=id)
            if listing.active == False:
                listings_ended.append(listing)
            else:
                listings_active.append(listing)
            return render(request, "auctions/home.html", {
                'user_id': id,
                'listings': listings_active,
                'sold': listings_ended,
                "categories": categories,
                'watchlist': watchlist
            })

    return render(request, "auctions/home.html", {
        'user_id': id,
        "categories": categories
    })


def listing(request, title):

    if request.method == "POST":
        return Http404

    else:
        try:
            listing = Listing.objects.get(title=title)
            comments = []
            comments_id = Listing.objects.values_list(
                'comments', flat=True).filter(title=title)
            for id in comments_id:
                if id is not None:
                    comment = Comment.objects.get(id=id)
                    comments.append(comment)

        except Listing.DoesNotExist:
            raise Http404("Listing Not Found")

        return render(request, "auctions/listing.html", {
            "title": title,
            "listing": listing,
            "biddingform": BiddingForm(),
            "addcommentsform": AddCommentsForm(),
            "comments": comments,
            "categories": categories
        })


@login_required
def bid(request, title):

    bidder = request.user

    if request.method == "POST":
        form = BiddingForm(request.POST)
        if form.is_valid():

            bidding_price = form.cleaned_data['bid']
            # Get the starting price of the listing
            listing = Listing.objects.get(title=title)

            if bidding_price >= listing.starting_bid:
                # get the existing bids
                bids = Listing.objects.values_list(
                    'bids', flat=True).filter(title=title)

                for bid in bids:

                    # if there's no bit yet,directly save the new bit
                    if bid is not None:
                        if bidding_price < bid:
                            RAISE_ERROR("Bid failed.")

                bid = Bid(item=listing, user=bidder,
                          offer=bidding_price)
                bid.save()
                # redirect user to the home page
                id = bidder.id
                return HttpResponseRedirect(reverse('home', args=[id]))

            # display error messages if bid failed
            return render(request, "auctions/listing.html", {
                "errormessage": "Cannot bid lower than the listing price nor exisiting bids.",
                "biddingform": BiddingForm(),
                "title": title,
                "categories": categories
            })

    return render(request, "auctions/listing.html", {
        "biddingform": BiddingForm()
    })

# User can add a listing to her wishlist


@login_required
def add_watchlist(request, title):
    listing = Listing.objects.get(title=title)
    user = request.user

    existing_watchlist = User.objects.values_list(
        'watchlists', flat=True).filter(username=user)
    for l in existing_watchlist:
        if l == listing:
            return render(request, 'auctions/listing.html', {
                "errormessagefromwatchlist": "This listing is already in your watchlist."
            })
        else:
            new_watchlist = Watchlist(user=user, item=listing)
            new_watchlist.save()
            id = user.id
            # TODO redirect user to the watchlist page
            return HttpResponseRedirect(reverse('home', args=[id]))


@login_required
def close_listing(request, title):
    bids = Listing.objects.values_list(
        'bids', flat=True).filter(title=title)
    highest_bid = max(bids)

    listing = Listing.objects.get(title=title)
    # Change the status of the listing to False
    listing.active = False
    if highest_bid is not None:
        listing.price_sold_for = highest_bid
    else:
        listing.price_sold_for = 0

    listing.save()
    # Find out the highest bidding, and show it to the user

    # Redirect to listing page
    return render(request, 'auctions/close.html', {
        "messages": "Close listing successful!",
        "highest_bid": highest_bid,
        "listing": listing,
        "title": title
    })


@login_required
def add_comments(request, title):

    if request.method == "POST":
        form = AddCommentsForm(request.POST)
        if form.is_valid():
            comments = form.cleaned_data['comments']
            # save the comment to the database
            comment = Comment(listing=Listing.objects.get(
                title=title), user=request.user, content=comments)
            comment.save()
        return HttpResponseRedirect(reverse('listing', args=[title]))

    return render(request, 'listing.html', {
        "addcommentsform": AddCommentsForm()
    })


def category(request, category):
    listings = Listing.objects.filter(category=category)
    categories = Listing.objects.values_list('category', flat=True)
    return render(request, 'auctions/category.html', {
        'listings': listings,
        'category': category,
        'categories': categories
    })
