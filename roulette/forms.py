from django import forms
from .models import Subject, Topic

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']
        widgets = {
            'name': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Fan nomini bu yerga kiriting',
                'class': 'form-control'
            }),
        }
        labels = {
            'name': 'Fan nomi',
        }

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Mavzu nomini kiriting',
                'class': 'form-control'
            }),
        }
        labels = {
            'name': 'Mavzu nomi',
        }