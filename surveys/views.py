import csv
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify

from .forms import SurveyMetaForm
from .models import Answer, Choice, Question, Response, Survey


def home(request):
    if request.user.is_authenticated:
        return redirect('surveys:dashboard')
    return render(request, 'surveys/home.html')


@login_required
def dashboard(request):
    surveys = request.user.surveys.all()
    active_count = sum(1 for s in surveys if s.is_active)
    return render(request, 'surveys/dashboard.html', {
        'surveys': surveys,
        'active_count': active_count,
        'closed_count': surveys.count() - active_count,
        'total_responses': sum(s.response_count for s in surveys),
    })


@login_required
def survey_builder(request, pk=None):
    survey = get_object_or_404(Survey, pk=pk, owner=request.user) if pk else None

    prefill_rows = []

    if request.method == 'POST':
        meta_form = SurveyMetaForm(request.POST, instance=survey)

        texts = request.POST.getlist('q_text')
        types = request.POST.getlist('q_type')
        requireds = request.POST.getlist('q_required')
        choices_raw = request.POST.getlist('q_choices')
        cond_idx = request.POST.getlist('q_condition_index')
        cond_choice_text = request.POST.getlist('q_condition_choice_text')

        rows = []
        for i, text in enumerate(texts):
            text = text.strip()
            if not text:
                continue
            rows.append({
                'row_index': i,
                'text': text,
                'type': types[i] if i < len(types) else Question.SINGLE,
                'required': (requireds[i] == '1') if i < len(requireds) else True,
                'choices': [c.strip() for c in (choices_raw[i] if i < len(choices_raw) else '').splitlines() if c.strip()],
                'condition_index': cond_idx[i] if i < len(cond_idx) and cond_idx[i] != '' else None,
                'condition_choice_text': cond_choice_text[i].strip() if i < len(cond_choice_text) else '',
            })
        prefill_rows = rows

        errors = []
        if not rows:
            errors.append("Ajoutez au moins une question à votre sondage.")
        for r in rows:
            if r['type'] in (Question.SINGLE, Question.MULTIPLE) and not r['choices']:
                errors.append(f"La question « {r['text']} » doit avoir au moins un choix de réponse.")

        if meta_form.is_valid() and not errors:
            with transaction.atomic():
                survey_obj = meta_form.save(commit=False)
                survey_obj.owner = request.user
                survey_obj.save()

                if survey is not None:
                    survey_obj.questions.all().delete()

                created_questions = {}
                created_choices = {}
                for order, r in enumerate(rows):
                    q = Question.objects.create(
                        survey=survey_obj,
                        text=r['text'],
                        question_type=r['type'],
                        order=order,
                        required=r['required'],
                    )
                    created_questions[r['row_index']] = q
                    for c_order, ctext in enumerate(r['choices']):
                        c = Choice.objects.create(question=q, text=ctext, order=c_order)
                        created_choices[(r['row_index'], ctext)] = c

                for r in rows:
                    if r['condition_index'] is None or not r['condition_choice_text']:
                        continue
                    try:
                        cond_row_index = int(r['condition_index'])
                    except (TypeError, ValueError):
                        continue
                    cond_q = created_questions.get(cond_row_index)
                    if not cond_q:
                        continue
                    cond_c = created_choices.get((cond_row_index, r['condition_choice_text']))
                    if cond_c:
                        q = created_questions[r['row_index']]
                        q.condition_question = cond_q
                        q.condition_choice = cond_c
                        q.save(update_fields=['condition_question', 'condition_choice'])

            messages.success(request, "Votre sondage a été enregistré avec succès.")
            return redirect('surveys:dashboard')
        else:
            for e in errors:
                messages.error(request, e)
    else:
        meta_form = SurveyMetaForm(instance=survey)
        if survey is not None:
            questions = list(survey.questions.all().prefetch_related('choices'))
            pk_to_index = {q.pk: i for i, q in enumerate(questions)}
            for i, q in enumerate(questions):
                prefill_rows.append({
                    'row_index': i,
                    'text': q.text,
                    'type': q.question_type,
                    'required': q.required,
                    'choices': [c.text for c in q.choices.all()],
                    'condition_index': pk_to_index.get(q.condition_question_id) if q.condition_question_id else None,
                    'condition_choice_text': q.condition_choice.text if q.condition_choice else '',
                })

    return render(request, 'surveys/survey_form.html', {
        'meta_form': meta_form,
        'survey': survey,
        'prefill_json': json.dumps(prefill_rows),
    })


@login_required
def survey_toggle_close(request, pk):
    survey = get_object_or_404(Survey, pk=pk, owner=request.user)
    if request.method == 'POST':
        survey.is_closed = not survey.is_closed
        survey.save(update_fields=['is_closed'])
        messages.success(request, f"Le sondage est maintenant {'clos' if survey.is_closed else 'actif'}.")
    return redirect('surveys:dashboard')


@login_required
def survey_delete(request, pk):
    survey = get_object_or_404(Survey, pk=pk, owner=request.user)
    if request.method == 'POST':
        title = survey.title
        survey.delete()
        messages.success(request, f"Le sondage « {title} » a été supprimé.")
    return redirect('surveys:dashboard')


def survey_detail(request, token):
    survey = get_object_or_404(Survey, share_token=token)

    if not survey.is_active:
        return render(request, 'surveys/survey_closed.html', {'survey': survey})

    if not survey.allow_anonymous and not request.user.is_authenticated:
        messages.info(request, "Connectez-vous pour répondre à ce sondage.")
        return redirect(f"{reverse('accounts:login')}?next={survey.get_absolute_url()}")

    questions = list(survey.questions.all().prefetch_related('choices'))

    if request.method == 'POST':
        submitted_choice_by_q = {}
        for q in questions:
            if q.is_choice_type:
                ids = request.POST.getlist(f'answer_{q.id}')
                submitted_choice_by_q[q.id] = {int(i) for i in ids if i.isdigit()}

        def is_visible(question):
            if not question.condition_question_id:
                return True
            parent_selected = submitted_choice_by_q.get(question.condition_question_id, set())
            return question.condition_choice_id in parent_selected

        errors = []
        answer_data = {}
        for q in questions:
            if not is_visible(q):
                continue
            if q.question_type == Question.TEXT:
                val = request.POST.get(f'answer_{q.id}', '').strip()
                if q.required and not val:
                    errors.append(f"« {q.text} » est obligatoire.")
                answer_data[q.id] = ('text', val)
            else:
                ids = submitted_choice_by_q.get(q.id, set())
                if q.required and not ids:
                    errors.append(f"« {q.text} » est obligatoire.")
                answer_data[q.id] = ('choice', ids)

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            resp = Response.objects.create(
                survey=survey,
                respondent=request.user if request.user.is_authenticated else None,
            )
            for q in questions:
                if q.id not in answer_data:
                    continue
                kind, val = answer_data[q.id]
                ans = Answer.objects.create(
                    response=resp, question=q,
                    text_answer=val if kind == 'text' else '',
                )
                if kind == 'choice' and val:
                    ans.choices.set(Choice.objects.filter(id__in=val, question=q))
            return redirect('surveys:thanks', token=token)

    return render(request, 'surveys/survey_detail.html', {'survey': survey, 'questions': questions})


def survey_thanks(request, token):
    survey = get_object_or_404(Survey, share_token=token)
    return render(request, 'surveys/survey_thanks.html', {'survey': survey})


@login_required
def survey_results(request, pk):
    survey = get_object_or_404(Survey, pk=pk, owner=request.user)
    charts = []
    text_blocks = []

    for q in survey.questions.all().prefetch_related('choices'):
        if q.is_choice_type:
            labels = []
            counts = []
            for c in q.choices.all():
                labels.append(c.text)
                counts.append(c.answers.filter(response__survey=survey).count())
            charts.append({
                'question': q,
                'chart_type': 'pie' if q.question_type == Question.SINGLE else 'bar',
                'labels_json': json.dumps(labels),
                'counts_json': json.dumps(counts),
                'total': sum(counts),
            })
        else:
            answers = Answer.objects.filter(question=q).exclude(text_answer='').select_related('response').order_by('-response__submitted_at')
            text_blocks.append({'question': q, 'answers': answers})

    return render(request, 'surveys/survey_results.html', {
        'survey': survey,
        'charts': charts,
        'text_blocks': text_blocks,
    })


@login_required
def survey_export_csv(request, pk):
    survey = get_object_or_404(Survey, pk=pk, owner=request.user)
    response = HttpResponse(content_type='text/csv')
    filename = slugify(survey.title) or 'sondage'
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    response.write('\ufeff')  # BOM pour Excel

    writer = csv.writer(response)
    questions = list(survey.questions.all())
    writer.writerow(['Date de soumission', 'Répondant'] + [q.text for q in questions])

    for resp in survey.responses.all().prefetch_related('answers__choices', 'answers__question').order_by('submitted_at'):
        answers_by_q = {a.question_id: a for a in resp.answers.all()}
        row = [
            resp.submitted_at.strftime('%Y-%m-%d %H:%M'),
            resp.respondent.username if resp.respondent else 'Anonyme',
        ]
        for q in questions:
            a = answers_by_q.get(q.id)
            row.append(a.display_value() if a else '')
        writer.writerow(row)

    return response
