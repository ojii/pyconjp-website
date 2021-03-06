import hashlib
import random

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

import account.views
import constance

from pycon.finaid.context_processors import financial_aid
import symposion.forms
from symposion.forms import LanguageForm
from symposion.proposals.models import ProposalSection


class SignupView(account.views.SignupView):

    form_class = symposion.forms.SignupForm

    def create_user(self, form, commit=True):
        user_kwargs = {
            "first_name": form.cleaned_data["first_name"],
            "last_name": form.cleaned_data["last_name"]
        }
        return super(SignupView, self).create_user(form, commit=commit,
                                                   **user_kwargs)

    def generate_username(self, form):
        def random_username():
            h = hashlib.sha1(form.cleaned_data["email"]).hexdigest()[:25]
            # don't ask
            n = random.randint(1, (10 ** (5 - 1)) - 1)
            return "%s%d" % (h, n)
        while True:
            try:
                username = random_username()
                User.objects.get(username=username)
            except User.DoesNotExist:
                break
        return username


class LoginView(account.views.LoginView):

    form_class = account.forms.LoginEmailForm


@login_required
def dashboard(request):
    if request.session.get("pending-token"):
        return redirect("speaker_create_token",
                        request.session["pending-token"])
    context = {'proposals_are_open': bool(ProposalSection.available()), }
    context.update(financial_aid(request))
    if constance.config.SHOW_LANGUAGE_SELECTOR:
        context['language_form'] = LanguageForm(
            initial={'language': request.LANGUAGE_CODE})
    return render(
        request, "dashboard.html",
        context,
    )


@require_POST
def change_language(request):
    form = LanguageForm(request.POST)
    if form.is_valid():
        language = form.cleaned_data['language']
        request.session['django_language'] = language
        if request.user.is_authenticated():
            account = request.user.account
            account.language = language
            account.save()

    return redirect(request.POST['next'])
