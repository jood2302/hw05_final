from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'cols': 40,
                'rows': 10,
                'name': 'text'
            }),
            'group': forms.Select(attrs={
                'class': 'form-control',
                'name': 'text',
            }),
            'image': forms.ImageField(),
        }

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Заполните текст.')
        return data