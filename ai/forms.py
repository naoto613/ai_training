from django import forms

class PhotoForm(forms.Form):
    image = forms.ImageField(widget=forms.FileInput(attrs={'class':'custom-file-input'}))

class UserForm(forms.Form):
    texttwo = forms.CharField(
        label='話す',
        widget=forms.TextInput(
            attrs={
                'id': 'dropedfile',
                'placeholder': 'ここに会話文を入力します。',
            }))