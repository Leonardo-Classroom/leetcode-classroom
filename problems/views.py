from django.core.paginator import Paginator
from django.shortcuts import render

from .filters import filter_problems
from .models import Problem, Tag


def is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def render_problem_browser(request, template_name, *, show_assign_action):
    """
    題目篩選/瀏覽頁共用的邏輯，後台派任務挑題頁跟學員瀏覽頁都用這個。
    如果是前端用 fetch() 帶 X-Requested-With 打過來的（篩選/換頁），
    只回傳結果區塊的 HTML 片段，讓前端動態換掉內容，不用整頁重新整理；
    一般直接開網址則回傳完整頁面。
    """
    qs = filter_problems(request.GET)
    paginator = Paginator(qs, 30)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "page_range": paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1),
        "tags": Tag.objects.all(),
        "difficulty_choices": Problem.Difficulty.choices,
        "selected_tags": [int(t) for t in request.GET.getlist("tags") if t.isdigit()],
        "selected_difficulties": request.GET.getlist("difficulty"),
        "q": request.GET.get("q", ""),
        "total_count": qs.count(),
        "show_assign_action": show_assign_action,
    }

    if is_ajax(request):
        return render(request, "partials/problem_results.html", context)
    return render(request, template_name, context)
