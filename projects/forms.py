from django import forms


class ContactForm(forms.Form):
    website = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"autocomplete": "off"}),
    )
    email = forms.EmailField(
        label="Your email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "you@example.com",
                "autocomplete": "email",
            }
        ),
    )
    subject = forms.CharField(
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Project inquiry",
            }
        ),
    )
    message = forms.CharField(
        min_length=10,
        max_length=4000,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "Tell me what you would like to build or discuss.",
                "rows": 7,
            }
        ),
    )

    def clean_website(self):
        website = self.cleaned_data.get("website")
        if website:
            raise forms.ValidationError("Leave this field blank.")
        return website
