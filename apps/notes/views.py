"""
View Layer: Renders templates and handles HTTP responses.
Bu dosya not işlemleri için template render işlemlerini yapar.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Note
from .forms import NoteForm
from .controllers import NoteController

@login_required
def note_list(request):
    controller = NoteController()
    context = controller.get_note_list_context(request)
    return render(request, 'notes/list.html', context)

@login_required
def note_detail(request, pk):
    controller = NoteController()
    context = controller.get_note_detail_context(request, pk)
    
    if context.get('error'):
        return redirect(context.get('redirect', 'notes:list'))
    
    return render(request, 'notes/detail.html', context)

@login_required
def note_create(request):
    controller = NoteController()
    
    if request.method == 'POST':
        form = NoteForm(request.POST, user=request.user)
        if form.is_valid():
            result = controller.create_note_context(request, form.cleaned_data)
            if result.get('success'):
                return redirect('notes:list')
            elif result.get('error'):
                return redirect(result.get('redirect', 'notes:list'))
    else:
        context = controller.create_note_context(request)
        if context.get('error'):
            return redirect(context.get('redirect', 'notes:list'))
        
        form = NoteForm(user=request.user, initial=context.get('initial_data', {}))
    
    context = controller.create_note_context(request)
    context['form'] = form
    return render(request, 'notes/form.html', context)

@login_required
def note_edit(request, pk):
    controller = NoteController()
    # MVC: Controller üzerinden notu ve izin kontrolünü al
    base_context = controller.update_note_context(request, pk)
    if base_context.get('error'):
        return redirect(base_context.get('redirect', 'notes:list'))
    
    note = base_context.get('note')
    
    if request.method == 'POST':
        # Mevcut not instance'ı ile formu bağla; unique_together hatalarını önler
        form = NoteForm(request.POST, user=request.user, instance=note)
        if form.is_valid():
            result = controller.update_note_context(request, pk, form.cleaned_data)
            if result.get('success'):
                return redirect('notes:detail', pk=pk)
            elif result.get('error'):
                return redirect(result.get('redirect', 'notes:list'))
    else:
        form = NoteForm(instance=note, user=request.user)
    
    base_context['form'] = form
    return render(request, 'notes/form.html', base_context)

@login_required
def note_delete(request, pk):
    controller = NoteController()
    context = controller.delete_note_context(request, pk)
    
    if context.get('error'):
        return redirect(context.get('redirect', 'notes:list'))
    
    if context.get('success'):
        return redirect('notes:list')
    
    return render(request, 'notes/delete.html', context)

@login_required
def get_students_by_course(request):
    """AJAX view to get students enrolled in a specific course"""
    controller = NoteController()
    return controller.get_students_by_course_ajax(request)
