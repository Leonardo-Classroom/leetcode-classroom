from .models import Problem


def filter_problems(params):
    """依 GET 參數快速篩選題目：q(關鍵字) / difficulty(可複選) / tags(可複選 tag id)"""
    qs = Problem.objects.all().prefetch_related("tags")

    q = params.get("q", "").strip()
    if q:
        qs = qs.filter(title__icontains=q)

    difficulties = params.getlist("difficulty")
    if difficulties:
        qs = qs.filter(difficulty__in=difficulties)

    tag_ids = [t for t in params.getlist("tags") if t.isdigit()]
    for tag_id in tag_ids:
        qs = qs.filter(tags__id=tag_id)

    return qs.distinct()
